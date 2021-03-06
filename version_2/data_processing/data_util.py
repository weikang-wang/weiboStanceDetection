# encoding=utf8
"""
    Author:  'jdwang'
    Date:    'create date: 2016-08-06'
    Email:   '383287471@qq.com'
    Describe:
"""
import pandas as pd
import numpy as np
from sklearn.metrics import f1_score


class DataUtil(object):
    def load_data(self,path):
        '''
            加载DataFrame格式的数据

        :param data: 数据
        :param path: 数据文件的路径
        :return: None
        '''
        data = pd.read_csv(
            path,
            sep='\t',
            header=0,
            encoding='utf8',
            index_col=0,
        )
        return data

    def save_data(self,data,path):
        '''
            保存DataFrame格式的数据

        :param data: 数据
        :param path: 数据文件的路径
        :return: None
        '''
        data.to_csv(path,
                    sep='\t',
                    header=True,
                    index=False,
                    encoding='utf8',
                    )

    def accuracy(self, true_result,predict_result):
        """
            预测,对输入的句子进行预测,并给出准确率
                1. 转换格式
                2. 统计准确率等
                3. 统计F1(macro) : 统计各个类别的F1值，然后进行Favor和Againist的宏平均

        :param true_result: 真实结果
        :type true_result: array-like
        :param predict_result: 预测结果
        :type predict_result: array-like
        :return: is_correct,accu,f1
        :rtype:tuple
        """


        is_correct = predict_result == true_result
        print('正确的个数:%d' % (sum(is_correct)))
        accu = sum(is_correct) / (1.0 * len(true_result))
        print('准确率为:%f' % (accu))
        f1 = f1_score(true_result, predict_result, average=None)
        print('F1为：%s' % (str(f1)))
        print('F1宏平均（Favor和Against）为：%s' % (str(np.average(f1[:-1]))))


        return is_correct, accu, f1

    def get_label_index(self):
        """
            获取 类类别的列表，总共有3类

        :return: label_to_index,index_to_label
        """

        index_to_label = [
            u'FAVOR',
            u'AGAINST',
            u'NONE',
        ]
        # print('类别数为：%d'%len(index_to_label))
        label_to_index = {label: idx for idx, label in enumerate(index_to_label)}
        return label_to_index, index_to_label

    def load_train_test_data(self,config):
        """
            加载训练数据和测试数据，根据配置选择
            加载的文件中一定要有的字段: 'ID','TARGET','TEXT', 'STANCE'

        :param config:
        :return:
        """

        train_data_file_path='/home/jdwang/PycharmProjects/weiboStanceDetection/version_2/dataset/TaskAA_all_data_2986.csv'
        test_data_file_path = '/home/jdwang/PycharmProjects/weiboStanceDetection/version_2/dataset/NLPCC_2016_Stance_Detection_gold/NLPCC_2016_Stance_Detection_Task_A_gold.utf8'

        # -------------- print start : just print info -------------
        if config['verbose'] > 0 :
            print('加载数据集的训练数据和测试数据')
            print('train_data_file_path:%s'%train_data_file_path)
            print('test_data_file_path:%s'%test_data_file_path)
        # -------------- print end : just print info -------------

        train_data = pd.read_csv(
            train_data_file_path,
            sep='\t',
            encoding='utf8',
            header=0
        )

        test_data = pd.read_csv(
            test_data_file_path,
            sep='\t',
            encoding='utf8',
            header=0
        )
        if config['verbose'] > 0:
            print('fit data shape is :%s' % (str(train_data.shape)))
            print('test data shape is :%s' % (str(test_data.shape)))


        train_data = train_data[['TARGET','TEXT', 'STANCE']]
        test_data = test_data[['TARGET','TEXT', 'STANCE']]

        label_to_index,index_to_label =self.get_label_index()

        train_data['STANCE_INDEX'] = train_data['STANCE'].map(label_to_index)
        test_data['STANCE_INDEX'] = test_data['STANCE'].map(label_to_index)

        return train_data,test_data




def check_result_with_gold_result():
    ''''
        # 检查当时比赛提交的结果里面，在 1000条 gold result中 准确率
        # 并结果保存（1000条），作为以后的baseline

    '''

    # 15000条 比赛提交结果
    data_subission_result = dutil.load_data('../dataset/NLPCC2016_Stance_Detection_Task_A_Result.txt')
    print(data_subission_result.head())
    # print(data_subission_result.shape)
    # 1000 条 gold result
    data_gold_result = dutil.load_data('../dataset/NLPCC_2016_Stance_Detection_gold/NLPCC_2016_Stance_Detection_Task_A_gold.utf8')


    print(data_gold_result.head())

    predicts = []
    is_correct = []
    for target,text,stance in data_gold_result.values:
        # print('%s'%(text))
        # print('%s'%(stance))
        submit_result = data_subission_result[data_subission_result['TEXT']==text].values[0][-1]
        predicts.append(submit_result)
        is_correct.append(submit_result==stance)

    dutil.accuracy(data_gold_result['STANCE'].as_matrix(), predicts)

    data_gold_result['PREDICT'] = predicts
    data_gold_result['IS_CORRECT'] = is_correct

    dutil.save_data(data_gold_result,'../result/baseline_result.csv')






if __name__ == '__main__':
    dutil = DataUtil()
    check_result_with_gold_result()