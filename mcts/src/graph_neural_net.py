#!/usr/bin/env python
# coding: utf-8
# GCN_v2.3.py

#Imports
import time
import torch
import torch.nn.functional as F
import matplotlib.pyplot as plt
import pickle
import numpy as np
from torch_geometric.data import Data
from torch_geometric.loader import DataLoader
from torch.nn import Linear
from torch_geometric.nn import global_max_pool
from torch_geometric.nn import GCNConv
from torch_geometric.nn import GENConv
from torchmetrics import R2Score

from bt_to_torch_data import *


#To read the pre-processed data from file
def getTorchData(new_path):
    data = []
    with open(new_path,'rb') as fr:
        try:
            while True:
                data.append(pickle.load(fr))
        except EOFError:
                pass
    return data


#Main GCN Class inherting from torch.nn
class GCN(torch.nn.Module):
    def __init__(self, dataset,hidden_channels):
        super(GCN, self).__init__()
        torch.manual_seed(48)
        self.conv1 = GCNConv(dataset[0].num_node_features, hidden_channels)
        self.conv2 = GCNConv(hidden_channels, hidden_channels)
        self.conv3 = GCNConv(hidden_channels, hidden_channels)
        self.lin = Linear(hidden_channels,1)

    def forward(self, x, edge_index, batch):
        # 1. Obtain node embeddings 
        x = self.conv1(x, edge_index)
        x = x.relu()
        x = self.conv2(x, edge_index)
        x = x.relu()
        x = self.conv3(x, edge_index)

        # 2. Readout layer
        x = global_max_pool(x, batch)  # [batch_size, hidden_channels]
        
        # 3. Apply a final classifier
#         x = F.dropout(x, p=0.5, training=self.training)
        x = self.lin(x)
        # x = F.softmax(x)
        return torch.sigmoid(x)
        return x


#Main GEN Class inherting from torch.nn
class GEN(torch.nn.Module):
    def __init__(self, dataset,hidden_channels):
        super(GEN, self).__init__()
        torch.manual_seed(48)
        self.conv1 = GENConv(dataset[0].num_node_features, hidden_channels)
        self.conv2 = GENConv(hidden_channels, hidden_channels)
        self.conv3 = GENConv(hidden_channels, hidden_channels)
        self.lin = Linear(hidden_channels,1)

    def forward(self, x, edge_index, batch):
        # 1. Obtain node embeddings 
        x = self.conv1(x, edge_index)
        x = x.relu()
        x = self.conv2(x, edge_index)
        x = x.relu()
        x = self.conv3(x, edge_index)

        # 2. Readout layer
        x = global_max_pool(x, batch)  # [batch_size, hidden_channels]
        
        # 3. Apply a final classifier
#         x = F.dropout(x, p=0.5, training=self.training)
        x = self.lin(x)
        # x = F.softmax(x)
        #return torch.sigmoid(x) #to get between 0 and 1
        return x




def train(model, train_loader, optimizer, criterion):
    avg_loss = []
    avg_r2 = []
    model.train()
    for data in train_loader: # Iterate in batches over the training dataset.
        optimizer.zero_grad() 
        out = model(data.x, data.edge_index, data.batch)# Perform a single forward pass.
        loss = criterion(out, data.y.resize_(data.y.size(dim=0),1))
        avg_loss.append(loss.detach().numpy())
        r2score = R2Score()
        r2 = r2score(out, data.y.resize_(data.y.size(dim=0),1))
        avg_r2.append(r2.detach().numpy())
        loss.backward()
        optimizer.step()
    return np.mean(avg_r2),np.mean(avg_loss)


def val(loader, model, criterion):
    avg_loss = []
    avg_r2 = []
    model.eval()
    for data in loader: # Iterate in batches over the validation dataset.
        out = model(data.x, data.edge_index, data.batch)# Perform a single forward pass.
        loss = criterion(out, data.y.resize_(data.y.size(dim=0),1))
        avg_loss.append(loss.detach().numpy())
        r2score = R2Score()
        r2 = r2score(out, data.y.resize_(data.y.size(dim=0),1))
        avg_r2.append(r2.detach().numpy())
    return np.mean(avg_r2),np.mean(avg_loss)

def main_train():

    #Define type of model (GCN,GEN) default: GCN
    type_of_model = 'GEN'


    #Reading project data
    new_path = 'nonterminal_data.p'
    project_data = getTorchData(new_path)


    # Normalize the y values (min is 0, max is 0.365)
    # project_data = []
    # for data in project_data:
    #     print(data.y)
    #     data.y = data.y/0.365


    # wait = input('wait')

    #Train-Val-Test split
    train_size = int(0.7 * len(project_data))
    val_size = int(0.1*len(project_data))
    test_size = len(project_data) - train_size - val_size
    print('Dataset size:', train_size+val_size+test_size)
    train_dataset,val_dataset, test_dataset = torch.utils.data.random_split(project_data, [train_size, val_size, test_size],generator=torch.Generator().manual_seed(48))
    print(f"Train: {len(train_dataset)}\nValidation: {len(val_dataset)}\nTest: {len(test_dataset)}")


    #Setting up data loaders
    batch_size = 100 #50
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=True)

    pickle.dump(test_loader, open('nonterminal_test_loader.p','wb'))

    #Model Setup
    if type_of_model == 'GEN':
        model = GEN(train_dataset,hidden_channels=8)
    else:
        model = GCN(train_dataset,hidden_channels=8)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    #criterion = torch.nn.MSELoss()
    criterion = torch.nn.L1Loss()

    #Training Loop
    start_time = time.time()
    r2_set = []
    loss_set = []
    val_r2_set = []
    val_loss_set = []
    num_epochs = 100
    for epoch in range(num_epochs):
        r2,loss = train(model,train_loader,optimizer, criterion)
        loss_set.append(loss)
        r2_set.append(r2)
        r2_val,loss_val = val(val_loader, model, criterion)
        val_loss_set.append(loss_val)
        val_r2_set.append(r2_val)
    total_time = time.time() - start_time
    print("RUNTIME: --- %s seconds ---" % (total_time))
    print("RUNTIME: --- %s minutes ---" % str((total_time)/60.0))
    print("RUNTIME: --- %s hours ---" % str((total_time)/3600.0))

    plot_performance(loss_set,val_loss_set,"Loss")
    plot_performance(r2_set,val_r2_set,"R2Score")
    print(val(test_loader, model, criterion))

    # Print model's state_dict
    # print("Model's state_dict:")
    # for param_tensor in model.state_dict():
    #     print(param_tensor, "\t", model.state_dict()[param_tensor].size())

    # # Print optimizer's state_dict
    # print("Optimizer's state_dict:")
    # for var_name in optimizer.state_dict():
    #     print(var_name, "\t", optimizer.state_dict()[var_name])


    torch.save(model.state_dict(), 'saved_model.pth')


def plot_performance(train_metric,val_metric,metric):    
    fig, ax1 = plt.subplots(figsize=(16,9))
    color = 'tab:red'
    ax1.plot(range(len(train_metric)), train_metric, c="blue", alpha=1, label=str("Train "+metric))
    ax1.plot(range(len(val_metric)), val_metric,c="red", label=str("Val "+metric))
    ax1.set_xlabel("Iterations")
    ax1.set_ylabel(str("Avg. "+metric), c=color)
    ax1.tick_params(axis='y', labelcolor=color)
    fig.tight_layout()  # otherwise the right y-label is slightly clipped
    ax1.legend(loc="center")
    #plt.show()
    plt.savefig(metric + '.png')


def test(loader,model):

    deltas = []
    for i in range (2000):
        data = loader.dataset[i]
        if data.y == 0:
            i+=1
        else:
            out = model(data.x, data.edge_index, data.batch)
            pred = out.detach().numpy().item(0)
            delta = abs(pred-data.y)
            deltas.append(delta)
            print(f"iter: {i} y: {data.y} pred: {pred} delta: {delta}")

    print('avg delta: ', sum(deltas)/len(deltas))

def test_with_zeros(loader, model):

    deltas = []
    for i in range (2000):
        data = loader.dataset[i]

        out = model(data.x, data.edge_index, data.batch)
        pred = out.detach().numpy().item(0)
        delta = abs(pred-data.y)
        deltas.append(delta)
        print(f"iter: {i} y: {data.y} pred: {pred} delta: {delta}")

    print('avg delta: ', sum(deltas)/len(deltas))


def main():

    # Get data
    new_path = 'nonterminal_data.p'
    project_data = getTorchData(new_path)

    # big = 0
    # big_i = 0
    # for i in range(len(project_data)):
    #     if project_data[i].y > big:
    #         big = project_data[i].y
    #         big_i = i
    #     # if project_data[i].y >= 0.2:
    #     #     print(i)
    #     #     break
    # print(big, big_i)

    #print(project_data[1056].y) #0.09
    # 1058, 0.27

    data_loader = DataLoader(project_data, batch_size=1, shuffle=True)

    test_path = 'nonterminal_test_loader_batch100.p'
    with open(test_path,'rb') as fr:
        test_loader = pickle.load(fr)

    print('test_loader',test_loader)
    #wait = input('bla')


    # Load model from save
    model = GEN(project_data,hidden_channels=8)
    model.load_state_dict(torch.load('saved_model.pth'))

    # Set to eval mode
    model.eval()

    # Input
    #single_bt_data = data_loader.batch
    #print(single_bt_data)
    ##single_bt_data = project_data[1058] 


    # Eval a single Data object that represents nonterminal BT/avg reward
    ##out = model(single_bt_data.x,single_bt_data.edge_index,None)
    ##print(out.data)

    # deltas = []
    # for i in range (10000):
    #     data = data_loader.dataset[i]
    #     if data.y == 0:
    #         i+=1
    #     else:
    #         out = model(data.x, data.edge_index, data.batch)
    #         pred = out.detach().numpy().item(0)
    #         delta = abs(pred-data.y)
    #         deltas.append(delta)
    #         print(f"iter: {i} y: {data.y} pred: {pred} delta: {delta}")

    # print('avg delta: ', sum(deltas)/len(deltas))

    #test(test_loader, model)
    test_with_zeros(test_loader, model)


    # y val, index, out (not normalized input data)
    # 0.09, 1056, 0.5134
    # 0.27, 1058, 0.5455 # THIS IS CONCERNING, why is it above, even when reward is below (see line below)
    # 0.365, 7273, 0.5239
    # 0, 0, 0.4978

# Functions for MCDAGS calls
def getModel():

    char_pickle_path = "/home/scheidee/Desktop/neural_mcdags_output/DATA/nonterminal1/nonterminal_char_words.p"
    nonterminal_chars = getGrammarData(char_pickle_path)

    pickle_path = "/home/scheidee/Desktop/neural_mcdags_output/DATA/nonterminal1/"
    file = '10000examples1654670294773nonterminal_'
    is_terminal_data = False
    converter = BT2TorchConversion(pickle_path,file,is_terminal_data, nonterminal_chars)

    new_path = 'nonterminal_data.p'
    project_data = getTorchData(new_path)

    model = GEN(project_data,hidden_channels=8)
    model.load_state_dict(torch.load('saved_model_batch100.pth'))

    # Set to eval mode
    model.eval()

    return model, converter

def getPrediction(model,nonterminal_bt_word, converter):

    torch_data_obj = converter.convertBTWord2TorchDataObject(nonterminal_bt_word)
    print('torch', torch_data_obj)

    return model(torch_data_obj.x, torch_data_obj.edge_index, None).item()


def MCDAGS_example():

    new_path = '/home/scheidee/Desktop/neural_mcdags_output/DATA/nonterminal1/10000examples1654670294773nonterminal_.p'

    data = []
    with open(new_path,'rb') as fr:
        try:
            while True:
                data.append(pickle.load(fr))
        except EOFError:
                pass

    # data is not torch yet
    word = data[0][0]
    print('word', word)
    print('reward', data[0][1])

    model, converter = getModel()
    print(model, converter)

    print(getPrediction(model,word,converter))



if __name__ == "__main__":

    #main_train()

    #main()

    MCDAGS_example()