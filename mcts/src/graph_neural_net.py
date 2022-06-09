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

#Define type of model (GCN,GEN) default: GCN
type_of_model = 'GEN'


#Reading project data
new_path = 'nonterminal_data.p'
project_data = getTorchData(new_path)


#Train-Val-Test split
train_size = int(0.7 * len(project_data))
val_size = int(0.1*len(project_data))
test_size = len(project_data) - train_size - val_size
print('Dataset size:', train_size+val_size+test_size)
train_dataset,val_dataset, test_dataset = torch.utils.data.random_split(project_data, [train_size, val_size, test_size],generator=torch.Generator().manual_seed(48))
print(f"Train: {len(train_dataset)}\nValidation: {len(val_dataset)}\nTest: {len(test_dataset)}")


#Setting up data loaders
batch_size = 100
train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=True)


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
#         x = F.softmax(x)
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
#         x = F.softmax(x)
        return x


#Model Setup
if type_of_model == 'GEN':
    model = GEN(train_dataset,hidden_channels=8)
else:
    model = GCN(train_dataset,hidden_channels=8)
optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
criterion = torch.nn.MSELoss()


def train():
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


def val(loader):
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


#Training Loop
start_time = time.time()
r2_set = []
mse_set = []
val_r2_set = []
val_mse_set = []
num_epochs = 100
for epoch in range(num_epochs):
    r2,mse = train()
    mse_set.append(mse)
    r2_set.append(r2)
    r2_val,mse_val = val(val_loader)
    val_mse_set.append(mse_val)
    val_r2_set.append(r2_val)
total_time = time.time() - start_time
print("RUNTIME: --- %s seconds ---" % (total_time))
print("RUNTIME: --- %s minutes ---" % str((total_time)/60.0))
print("RUNTIME: --- %s hours ---" % str((total_time)/3600.0))


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


# fig, ax1 = plt.subplots(figsize=(16,9))
# color = 'tab:red'
# ax1.plot(range(len(mse_set)), mse_set, c="blue", alpha=1, label=str("Train "+"MSE"))
# ax1.plot(range(len(val_mse_set)), val_mse_set,c="red", label=str("Val "+"MSE"))
# ax1.set_xlabel("Iterations")
# ax1.set_ylabel(str("Avg. "+"MSE"), c=color)
# ax1.tick_params(axis='y', labelcolor=color)
# fig.tight_layout()  # otherwise the right y-label is slightly clipped
# ax1.legend(loc="center")
# # plt.show()
# plt.savefig('mse.png')


plot_performance(mse_set,val_mse_set,"MSE")
plot_performance(r2_set,val_r2_set,"R2Score")
print(val(test_loader))


# Print model's state_dict
# print("Model's state_dict:")
# for param_tensor in model.state_dict():
#     print(param_tensor, "\t", model.state_dict()[param_tensor].size())

# # Print optimizer's state_dict
# print("Optimizer's state_dict:")
# for var_name in optimizer.state_dict():
#     print(var_name, "\t", optimizer.state_dict()[var_name])


torch.save(model.state_dict(), 'saved_model.pth')


