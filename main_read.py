# -*- coding = utf-8 -*-
# @Time : 2022/4/26 0026 16:31
# @Author : 小白
# @File : main.py
# @Software : PyCharm

import torch.nn as nn
import argparse
import config
from BCNN_fc import BCNN_fc
from BCNN_all import BCNN_all
import torch.backends.cudnn as cudnn
from load import *

# 配置GPU
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
transform_train = transforms.Compose([
        transforms.Resize((448, 448)),
        transforms.RandomCrop(448, padding=4),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize([0.485,0.456,0.406], [0.229,0.224,0.225]),
    ])
dataset = CUB(root='./CUB_200_2011', is_train=False, transform=transform_train,)
trainloader = torch.utils.data.DataLoader(dataset, batch_size=2, shuffle=True, num_workers=0,
                                              drop_last=True)
cudnn.benchmark = True

# 主程序
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='network_select')
    parser.add_argument('--net_select',
                        dest='net_select',
                        default='BCNN_all',
                        help='select which net to train/test.')
    args = parser.parse_args()
    if args.net_select == 'BCNN_fc':
        net = BCNN_fc().to(device)
    else:net = BCNN_all().to(device)
    model_path = os.listdir("./model")
    model_path = model_path[len(model_path) - 1]
    # print(model_path)
    if model_path[13] == '.':
        now_epoch = int(model_path[12])
        # print(now_epoch)
    elif model_path[15] != '.':
        now_epoch = int(model_path[12:14])
        # print(now_epoch)
    net.load_state_dict(torch.load('./model/'+model_path))
    print(net)

    #损失
    criterion = nn.CrossEntropyLoss().cuda()
    optimizer = torch.optim.SGD(net.fc.parameters(),
                                lr=config.BASE_LEARNING_RATE,
                                momentum=0.9,
                                weight_decay=config.WEIGHT_DECAY)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        mode='max',
        factor=0.1,
        patience=3,
        verbose=True,
        threshold=1e-4
    )

    # 训练模型
    print('Start Training ==>')
    total_step = len(trainloader)
    best_acc=0.0
    best_epoch=None
    for epoch in range(now_epoch, config.EPOCHS):
        epoch_loss=[]
        num_correct=0
        num_total=0
        for i, (images, labels) in enumerate(trainloader):
            # 数据转为cuda
            images = torch.autograd.Variable(images.cuda())
            labels = torch.autograd.Variable(labels.cuda())
            # 梯度清零
            optimizer.zero_grad()
            # 前向传播
            outputs = net(images)
            loss = criterion(outputs, labels)
            # 预测
            _, prediction = torch.max(outputs.data, 1)
            num_total += labels.size(0)
            num_correct += torch.sum(prediction == labels.data)
            # 后向传播
            loss.backward()
            optimizer.step()
            if (i + 1) % 10 == 0:
                print('Epoch [{}/{}], Step [{}/{}], Training Loss: {:.4f}'.format(
                    epoch + 1, config.EPOCHS, i+1, total_step, loss.item()))
        train_Acc = 100*num_correct/num_total
        torch.save(net.state_dict(), config.PATH['model'] + 'vgg16_epoch_%d.pth' % (epoch + 1))
