"""
Created on 20 Sep, 2020

@author: Xiaokun Zhang
"""
# import required lib and files....
import os
import time
import random
import argparse
import pickle
import pandas as pd
import numpy as np
from tqdm import tqdm
from os.path import join
os.environ['CUDA_LAUNCH_BLOCKING'] = '1'
import torch
from torch import nn
from torch.utils.data import DataLoader
import torch.nn.functional as F
import torch.optim as optim
from torch.optim.lr_scheduler import StepLR
from torch.autograd import Variable
from torch.backends import cudnn
import DIDN.metric
from DIDN.DIDN.utils import collate_fn
from DIDN.DIDN.didn import *
from DIDN.DIDN.dataset import load_data, RecSysDataset
from DIDN.accuracy_measures import *
from DIDN.Data_preprocessing import *
from DIDN.data_cleaning_DIGI import *
# baseline model....
from DIDN.baselines.stan.main_stan import *
from DIDN.baselines.vstan.main_vstan import *
from DIDN.baselines.sfcknn.main_sfcknn import *
from DIDN.baselines.SR.main_sr import *
# stop python warnings....
import warnings
warnings.filterwarnings("ignore")
parser = argparse.ArgumentParser()
parser.add_argument('--dataset', default='diginetica', help='diginetica/yoochoose1_4/yoochoose1_64')
parser.add_argument('--batch_size', type=int, default=512, help='input batch size 512')
parser.add_argument('--hidden_size', type=int, default=64, help='hidden state size of gru module')
parser.add_argument('--embed_dim', type=int, default=64, help='the dimension of item embedding')
parser.add_argument('--epoch', type=int, default=50, help='the number of epochs to train for 100')
parser.add_argument('--lr', type=float, default=0.001, help='learning rate')
parser.add_argument('--lr_dc', type=float, default=0.1, help='learning rate decay rate')
parser.add_argument('--lr_dc_step', type=int, default=80,
                    help='the number of steps after which the learning rate decay')
parser.add_argument('--test', default=False, help='test')
parser.add_argument('--topk', type=int, default=20, help='number of top score items selected for calculating recall and mrr metrics')
parser.add_argument('--valid_portion', type=float, default=0.1,
                    help='split the portion of training set as validation set')
parser.add_argument('--position_embed_dim', type=int, default=64, help='the dimension of position embedding')
parser.add_argument('--max_len', type=float, default=19, help='max length of input session')
parser.add_argument('--alpha1', type=float, default=0.1, help='degree of alpha pooling')
parser.add_argument('--alpha2', type=float, default=0.1, help='degree of alpha pooling')
parser.add_argument('--alpha3', type=float, default=0.1, help='degree of alpha pooling')
parser.add_argument('--pos_num', type=int, default=2000, help='the number of position encoding')
parser.add_argument('--neighbor_num', type=int, default=5, help='the number of neighboring sessions')
parser.add_argument('--topkkk', type=float, default=[10, 20], help='learning rate') 
parser.add_argument('--validation_session', type=float, default=10000, help='learning rate')
parser.add_argument('--MRR', type=float, default=[10, 20], help='learning rate') 
parser.add_argument('--Recall', type=float, default=[10, 20], help='learning rate') 
args = parser.parse_args()
print(args)
here = os.path.dirname(os.path.abspath(__file__))
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print("<<<<<<<<<<<<<<<<  "+args.dataset+" >>>>>>>>>>>>>>>>>>>>")
data_path = Path("data/")
data_path = data_path.resolve()
result_path = Path("results/")
result_path = result_path.resolve()

if torch.cuda.is_available():
    torch.cuda.set_device(0)
def run_experiments_for_DIDN():
    print('Loading data...')
    if args.dataset == "diginetica":
        
        name = "train-item-views.csv"
        obj1 = Data_processing(dataset = args.dataset, path = data_path / name)
        tra_sess, tes_sess, sess_clicks = obj1.data_load()
        tra_ids, tra_dates, tra_seqs = obj1.obtian_tra(tra_sess, sess_clicks)
        tes_ids, tes_dates, tes_seqs = obj1.obtian_tes(tes_sess, sess_clicks)

        tr_seqs, tr_dates, tr_labs, tr_ids = obj1.process_seqs_train(tra_seqs, tra_dates)
        te_seqs, te_dates, te_labs, te_ids = obj1.process_seqs_test(tes_seqs, tes_dates)
        
        n_items = len(obj1.item_dict) + 1
        train_data = (tr_seqs, tr_labs)
        test_data = (te_seqs, te_labs)
        
    if args.dataset in ['yoochoose1_64', 'yoochoose1_4']:
        name = "yoochoose-clicks.dat"
        obj1 = Data_processing(dataset = args.dataset, path = data_path / name)
        tra_sess, tes_sess, sess_clicks = obj1.data_load()
        tra_ids, tra_dates, tra_seqs = obj1.obtian_tra(tra_sess, sess_clicks)
        tes_ids, tes_dates, tes_seqs = obj1.obtian_tes(tes_sess, sess_clicks)
        tr_seqs, tr_dates, tr_labs, tr_ids = obj1.process_seqs_train(tra_seqs, tra_dates)
        te_seqs, te_dates, te_labs, te_ids = obj1.process_seqs_test(tes_seqs, tes_dates)
        n_items = len(obj1.item_dict) + 1
        
        train_data = (tr_seqs, tr_labs)
        test_data = (te_seqs, te_labs)

    vali_train, test_valid = load_data(train_data, test_data, valid_portion=args.valid_portion)
    vali_train = RecSysDataset(vali_train)
    test_valid = RecSysDataset(test_valid)
    valid_train_loader = DataLoader(vali_train, batch_size=args.batch_size, shuffle=True, collate_fn=collate_fn)
    valid_test_loader = DataLoader(test_valid, batch_size=1, shuffle=False, collate_fn=collate_fn)
    
    model = DIDN(n_items, args.hidden_size, args.embed_dim, args.batch_size, args.max_len, args.position_embed_dim, args.alpha1, args.alpha2, args.alpha3,args.pos_num, args.neighbor_num).to(device)
    optimizer = optim.Adam(model.parameters(), args.lr)
    criterion = nn.CrossEntropyLoss()
    scheduler = StepLR(optimizer, step_size=args.lr_dc_step, gamma=args.lr_dc)
    early_stopping =  EarlyStopping()
    for epoch in tqdm(range(args.epoch)):
        # train for one epoch
        scheduler.step(epoch=epoch)
        model = modelTraining(valid_train_loader, model, optimizer, epoch, args.epoch, criterion, log_aggr=200)
        performance_measures = validation(model, valid_test_loader, validation = True)
        print("<<<<<<<<<<<<<<<<<<<<< Current best score: "+str(early_stopping.best_score)+" >>>>>>>>>>>>>>>>>>>>>>>")
        early_stopping(performance_measures['Recall_20'].score(), epoch)
        print("<<<<<<<<<<<<<<<<<<<<< Counter value: "+str(early_stopping.counter)+" >>>>>>>>>>>>>>>>>>>>>>>")
        print("<<<<<<<<<<<<<<<<<<<<< Current score: "+str(performance_measures['Recall_20'].score())+" >>>>>>>>>>>>>>>>>>>>>>>")
        print("<<<<<<<<<<<<<<<<<<<<< New best score: "+str(early_stopping.best_score)+" >>>>>>>>>>>>>>>>>>>>>>>")

        if early_stopping.early_stop:
            print("Early stopping")
            break

    train_full, test = load_data(train_data, test_data)
    train_loader = RecSysDataset(train_full)
    test_loader = RecSysDataset(test)
    train_loader = DataLoader(train_loader, batch_size=args.batch_size, shuffle=True, collate_fn=collate_fn)
    test_loader = DataLoader(test_loader, batch_size=1, shuffle=False, collate_fn=collate_fn)    
    for epoch in tqdm(range(early_stopping.epoch + 1)):
        # train for one epoch
        scheduler.step(epoch=epoch)
        model = modelTraining(train_loader, model, optimizer, epoch, args.epoch, criterion, log_aggr=200)
    performance_measures = validation(model, test_loader)
    
    df = pd.DataFrame()
    for key in performance_measures:
        print(key +"   "+str(performance_measures[key].score()))
        df[key] = [performance_measures[key].score()]
    name = "DIDN_"+args.dataset+".txt"
    df.to_csv(data_path / name)

# function for modeling training.....
def modelTraining(train_loader, model, optimizer, epoch, num_epochs, criterion, log_aggr=1):
    model.train()
    sum_epoch_loss = 0

    start = time.time()
    for i, (seq, target, lens) in tqdm(enumerate(train_loader), total=len(train_loader)):
        seq = seq.to(device)
        target = target.to(device)
        # neighbors = neighbors.to(device)
        optimizer.zero_grad()
        outputs = model(seq, lens)
        loss = criterion(outputs, target)
        loss.backward()
        optimizer.step()

        loss_val = loss.item()
        sum_epoch_loss += loss_val
        iter_num = epoch * len(train_loader) + i + 1
        if i % log_aggr == 0:
            print('[TRAIN] epoch %d/%d batch loss: %.4f (avg %.4f) (%.2f im/s)'
                  % (epoch + 1, num_epochs, loss_val, sum_epoch_loss / (i + 1),
                     len(seq) / (time.time() - start)))
        start = time.time()
        
    return model

def validation(model, valid_loader, validation = False):
    # intialize MRR class
    performance_measures = dict()
    for i in args.topkkk:
        performance_measures["MRR_"+str(i)] = MRR(i)
        performance_measures["Pre_"+str(i)] = Precision(i)
        performance_measures["Recall_"+str(i)] = Recall(i)

    model.eval()
    users = 0
    with torch.no_grad():
        for seq, target, lens in tqdm(valid_loader):
            users+=1
            seq = seq.to(device)
            target = target.to(device)
            outputs = model(seq, lens)
            logits = F.softmax(outputs, dim = 1)
            logits = logits.topk(200)[1]
            logits = logits.detach().cpu().numpy()
            logits = np.ravel(logits)
            target = target.detach().cpu().numpy()
            recommendation_list = pd.Series([0 for i in range(len(logits))], index = logits)
            # Calculate the MRR values
            for key in performance_measures:
                performance_measures[key].add(recommendation_list, target[0])
            
            if validation == True and args.validation_session == users:
                break
    return performance_measures

if __name__ == '__main__':
    
    print("Experiments are runinig for DIDN model................... wait for results...............")
    run_experiments_for_DIDN()
    
    print("Experiments are runing for each model. After execution, the results will be saved into *results*. Thanks for patience.")
    print("Experiments are runinig for SR model................... wait for results...............")
    se_obj = SequentialRulesMain(data_path, result_path, dataset = args.dataset)
    se_obj.fit_(args.topkkk)
    
    # # SFCKNN
    print("Experiments are runinig for SFCKNN model................... wait for results...............")
    sfcknn_obj = SFCKNN_MAIN(data_path, result_path, dataset = args.dataset)
    sfcknn_obj.fit_(args.topkkk)
    
    print("Experiments are runinig for STAN model................... wait for results...............")
    stan_obj = STAN_MAIN(data_path, result_path, dataset = args.dataset)
    stan_obj.fit_(args.topkkk)
    # # VSTAN method........
    print("Experiments are runinig for VSTAN model................... wait for results...............")
    vstan_obj = VSTAN_MAIN(data_path, result_path, dataset = args.dataset)
    vstan_obj.fit_(args.topkkk)
    
    
