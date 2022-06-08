#!/usr/bin/env python
# coding: utf-8

# In[1]:


#Installing dependencies
get_ipython().system('pip install torch_geometric')
get_ipython().system('pip install torch_sparse')
get_ipython().system('pip install torch_scatter')
get_ipython().system('pip install torchmetrics')


# In[2]:


#Imports
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
from torchmetrics import R2Score


# In[3]:


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


# In[4]:


#Reading project data
new_path = 'project_data_v2.p'
project_data = getTorchData(new_path)


# In[5]:


#Train-Val-Test split
train_size = int(0.7 * len(project_data))
val_size = int(0.1*len(project_data))
test_size = int(0.2*len(project_data))
print(train_size+val_size+test_size)
train_dataset,val_dataset, test_dataset = torch.utils.data.random_split(project_data, [train_size, val_size, test_size],generator=torch.Generator().manual_seed(48))
print(f"Dataset Size\nTrain: {len(train_dataset)}\nValidation: {len(val_dataset)}\nTest: {len(test_dataset)}")


# In[6]:


#Setting up data loaders
batch_size = 100
train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=True)


# In[7]:


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


# In[8]:


#Model Setup
model = GCN(train_dataset,hidden_channels=16)
optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
criterion = torch.nn.MSELoss()


# In[9]:


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
        


# In[10]:


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
    


# In[11]:


#Training Loop
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
# plt.plot(range(num_epochs),mse_set)
# plt.show()
# plt.plot(range(num_epochs),r2_set)


# In[12]:


def plot_performance(train_metric,val_metric,metric):    
    fig, ax1 = plt.subplots(figsize=(16,9))
    color = 'tab:red'
    ax1.plot(range(len(train_metric)), train_metric, c="blue", alpha=1, label=str("Train "+metric))
    ax1.plot(range(len(val_metric)), val_metric,c="red", label=str("Train "+metric))
    ax1.set_xlabel("Iterations")
    ax1.set_ylabel(str("Avg. "+metric), c=color)
    ax1.tick_params(axis='y', labelcolor=color)
    fig.tight_layout()  # otherwise the right y-label is slightly clipped
    ax1.legend(loc="center")
    plt.show()


# In[13]:


plot_performance(mse_set,val_mse_set,"MSE")


# In[14]:


plot_performance(r2_set,val_r2_set,"R2Score")


# In[15]:


print(val(test_loader))


# In[ ]:
