#encoding=utf8
import pandas as pd
import logging
import jieba
import re
import itertools
import numpy as np
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s',
                    level=logging.DEBUG
                    )
# 最大句子填充完长度
MAX_SENTENCE_LENGTH = 173


def data_detail(data):
    '''
    展示数据的详细信息
    :param data: Dateframe对象
    :return: 无
    '''
    logging.debug('data的个数为：%d'%(len(data)))
    logging.debug('data的sample数据：')
    logging.debug( data.head())

    logging.debug('data的target和个数分别为：')
    logging.debug(data['TARGET'].value_counts())
    logging.debug('统计每个Target下各个类型立场的数量...')
    group = data.groupby(by=['TARGET','STANCE'])
    logging.debug( group.count())

    logging.debug('数据各个字段情况...')
    # print data.info()
    for column in data.columns:
        count_null = sum(data[column].isnull())
        if count_null!=0:
            logging.warn('%s字段有空值，个数：%d'%(column,count_null))
            null_data_path = './null_data.csv'
            logging.warn('将缺失值数据输出到文件：%s'%(null_data_path))
            data[data[column].isnull()].to_csv(null_data_path,
                                               index=None,
                                               sep='\t')


def processing_na_value(data,clear_na=True,fill_na = False,fill_char = 'NULL'):
    '''
    处理数据的空值
    :param data:  Dateframe对象
    :param clear_na: bool,是否去掉空值数据
    :param fill_na: bool，是否填充空值
    :param fill_char: str，填充空置的字符
    :return: Dateframe对象
    '''
    for column in data.columns:
        count_null = sum(data[column].isnull())
        if count_null != 0:
            logging.warn('%s字段有空值，个数：%d' % (column, count_null))
            if clear_na:
                logging.warn('对数据的%s字段空值进行摘除'%(column))
                data = data[data[column].notnull()]
            else:
                if fill_na:
                    logging.warn('对数据的%s字段空值进行填充，填充字符为：%s'%(column,fill_char))
                    data[column] = data[column].fillna(value=fill_char)
    return data

def split_train_test(data,train_split = 0.7):
    '''
    将数据切分成训练集和验证集
    :param data:
    :param train_split: float，取值范围[0,1],设置训练集的比例
    :return: dev_data,test_data
    '''
    logging.debug('对数据随机切分成train和test数据集，比例为：%f'%(train_split))
    num_train = len(data)
    num_dev = int(num_train * train_split)
    num_test = num_train - num_dev
    logging.debug('全部数据、训练数据和测试数据的个数分别为：%d,%d,%d'%(num_train,num_dev,num_test))
    rand_list = np.random.RandomState(0).permutation(num_train)
    # print rand_list
    # print rand_list[:num_dev]
    # print rand_list[num_dev:]
    dev_data = data.iloc[rand_list[:num_dev]].sort_index()
    test_data = data.iloc[rand_list[num_dev:]].sort_index()
    # print dev_data
    # print test_data
    return dev_data,test_data

def clean_data(data):
    logging.debug('开始清理数据...')
    # 原始句子列表
    origin_sentences = data['TEXT']
    # print origin_sentences
    # 使用正则过滤掉非中文的字符
    pattern = re.compile(u'[^\u4e00-\u9fa5]+')
    filter_not_chinese_text = lambda x : pattern.sub(' ',x.decode('utf8'))
    clean_sentences = origin_sentences.apply(filter_not_chinese_text)
    # 分词处理
    segment_text = lambda x:\
        ','.join([item for item in jieba.cut(x,cut_all=True) if len(item.strip())!=0])
    segment_sentences = clean_sentences.apply(segment_text)

    data['CLEAN_SENTENCES'] = clean_sentences
    data['SEGMENT_SENTENCES'] = segment_sentences
    max_length = max([len(item.split(',')) for item in segment_sentences])
    logging.debug(u'最长' +','.join([item for item in segment_sentences if len(item.split(',')) ==max_length]))
    logging.debug('最大句子长度为%d'%(max_length))
    # 检查过滤后，是否出现空句子
    for i, items in enumerate(clean_sentences):
        # print items
        if len(items.strip())==0:
            logging.warn('第%d句在过滤后出现空句子'%(i+1))

    return data


def to_vector(data):
    '''
    将为data中句子生成句子向量，并返回字典频率、target正、负、中的概率等
    :param data:
    :return: data,(freq_pos,freq_neg,freq_non),target_dict
    '''
    logging.debug('开始转换数据成向量的形式...')
    sentences = [item.split(',') for item in data['SEGMENT_SENTENCES']]

    dictionary = set(itertools.chain(*sentences))
    # 由于部分句子过滤后出现空串，所以字典会出现空串，这里将空串这个移除
    # 暂且不去掉，作为一个特殊符号保存
    # dictionary.remove('')
    dict_size = len(dictionary)
    logging.debug('字典大小为：%d'%(dict_size))
    idx2word = list(dictionary)
    word2idx = { item:idx for idx,item in enumerate(dictionary)}
    # print word2idx
    sentence_to_index = lambda x : [word2idx.get(item,-1) for item in x]
    indexs = [ sentence_to_index(items) for items in sentences]
    # print indexs[0]
    vectors = []
    for items in indexs:
        temp = np.zeros(dict_size,dtype=int)
        temp[items]=1
        vectors.append(temp)
    vectors = np.array(vectors)

    logging.debug('向量shape：%d,%d'%( vectors.shape))
    # print data.head()
    count_pos = sum(vectors[(data['STANCE']=='FAVOR').as_matrix()])
    count_neg = sum(vectors[(data['STANCE']=='AGAINST').as_matrix()])
    count_non = sum(vectors[(data['STANCE']=='NONE').as_matrix()])
    count_all = sum(vectors)
    pos_word =  [i for i,item in enumerate(count_pos) if item!=0]
    neg_word =  [i for i,item in enumerate(count_neg) if item!=0]
    non_word =  [i for i,item in enumerate(count_non) if item!=0]
    # logging.debug('正例中出现的词有%d个'%(len(pos_word)))
    # logging.debug('负例中出现的词有%d个'%(len(neg_word)))
    # logging.debug('中立中出现的词有%d个'%(len(non_word)))
    logging.debug(u'正例词(%d个):'%(len(pos_word))+ ','.join([idx2word[i] for i in pos_word]))
    logging.debug(u'负例词(%d个):'%(len(neg_word)) + ','.join([idx2word[i] for i in neg_word]))
    logging.debug(u'中立词(%d个):'%(len(non_word)) +','.join([idx2word[i] for i in non_word]))

    freq_pos = count_pos/(count_all*1.0)
    freq_neg = count_neg/(count_all*1.0)
    freq_non = count_non/(count_all*1.0)
    # print freq_pos
    # print freq_neg
    # print freq_non
    index_to_freq = lambda x:np.asarray([[freq_pos[item],freq_neg[item],freq_non[item]] for item in x])
    sentences_freqs = [index_to_freq(item) for item in indexs]

    # print sentences_freqs[0].shape
    # 统计每个Target下各个类型立场的数量
    group = data.groupby(by=['TARGET'])
    target_dict = {}
    for target,g in group:
        # print target
        g_count_pos =  sum(g['STANCE'] == 'FAVOR')
        g_count_neg =  sum(g['STANCE'] == 'AGAINST')
        g_count_non =  sum(g['STANCE'] == 'NONE')
        g_count_all = len(g)
        target_dict[target] = np.array([g_count_pos,g_count_neg,g_count_non])/(g_count_all*1.0)
        # print target_dict[target]

    vector_prob = []
    # 原始句子最大长度172,所有句子补全为173长度的句子
    max_sentence_length = MAX_SENTENCE_LENGTH
    for target,sent in zip(data['TARGET'],sentences_freqs):
        # print len(sent)
        if len(sent)<max_sentence_length:
            # print len(sent)
            padding_length = max_sentence_length - len(sent)

            # print '需要填充%d'%(padding_length)
            sentence_after_padding = np.concatenate([sent,padding_length*[target_dict[target]]])
            vector_prob.append(sentence_after_padding)
            # print sentence_after_padding
            # print len(sentence_after_padding)
    # quit()
    # print len(vector_prob)
    vector_prob = [item.flatten() for item in vector_prob]
    array_to_str = lambda x: ','.join(['%.5f' % (item) for item in x])
    vector_prob = [array_to_str(item) for item in vector_prob]
    data['VECTOR_PROB'] = vector_prob

    return data,word2idx,(freq_pos,freq_neg,freq_non),target_dict

def testdata_to_vector(data,word2idx,freq,target_dict):
    '''
    生成句子向量，使用已有的字典等
    :param data:
    :param freq: (freq_pos,freq_neg,freq_non)
    :param target_dict:
    :return:
    '''
    freq_pos, freq_neg, freq_non = freq
    # 增加一个元素在最后的原因，是预留给OOV的词的，如果该词是OOV，则赋予概率为0
    freq_pos.__add__(0)
    freq_neg.__add__(0)
    freq_non.__add__(0)
    logging.debug('开始使用已有字典转换数据成向量的形式...')
    sentences = [item.split(',') for item in data['SEGMENT_SENTENCES']]
    word_to_freq = lambda x: \
        np.asarray([[freq_pos[word2idx.get(item,-1)], freq_neg[word2idx.get(item,-1)], freq_non[word2idx.get(item,-1)]] for item in x])
    sentences_freqs = [word_to_freq(item) for item in sentences]
    # 对句子补全
    vector_prob = []
    # 句子最大长度172,所有句子补全为173长度的句子
    max_sentence_length = MAX_SENTENCE_LENGTH
    for target, sent in zip(data['TARGET'], sentences_freqs):
        # print len(sent)
        if len(sent) < max_sentence_length:
            # print len(sent)
            padding_length = max_sentence_length - len(sent)

            # print '需要填充%d'%(padding_length)
            sentence_after_padding = np.concatenate([sent, padding_length * [target_dict[target]]])
            vector_prob.append(sentence_after_padding)
            # print sentence_after_padding
            # print len(sentence_after_padding)
    # print len(vector_prob)
    # print vector_prob[0].shape
    # quit()
    vector_prob = [item.flatten() for item in vector_prob]
    array_to_str = lambda x: ','.join(['%.5f' % (item) for item in x])
    vector_prob = [array_to_str(item) for item in vector_prob]
    # print vector_prob[0]


    data['VECTOR_PROB'] = vector_prob
    return data



def main_processing_dataA():
    '''
    dataA的主处理过程
    :return:
    '''
    train_dataA_file_path = '/home/jdwang/PycharmProjects/weiboStanceDetection/train_data/' \
                            'evasampledata4-TaskAA.txt'


    train_dataA = pd.read_csv(train_dataA_file_path,
                              sep='\t',
                              header=0)
    logging.debug('show the detail of task A')
    # data_detail(train_dataA)
    # 处理空值数据
    train_dataA = processing_na_value(train_dataA,
                                      clear_na=False,
                                      fill_na=True,
                                      fill_char='NONE')

    train_dataA = clean_data(train_dataA)

    dev_dataA, test_dataA = split_train_test(train_dataA, train_split=0.7)
    #
    dev_dataA,word2idx,freq,target_dict = to_vector(dev_dataA)
    # print train_dataA.head()
    test_dataA = testdata_to_vector(test_dataA,word2idx,freq,target_dict)
    # print test_dataA.head()

    # print dev_dataA.head()
    dev_dataA_result_path = '/home/jdwang/PycharmProjects/weiboStanceDetection/train_data/' \
                              'dev_data.csv'
    logging.debug('将dev data集保存到：%s'%(dev_dataA_result_path))
    dev_dataA.to_csv(dev_dataA_result_path,
                       sep='\t',
                       index=None,
                       encoding='utf8'
                       )
    # print dev_dataA.shape
    test_dataA_result_path = '/home/jdwang/PycharmProjects/weiboStanceDetection/train_data/' \
                              'test_data.csv'
    logging.debug('将test data集保存到：%s'%(test_dataA_result_path))
    test_dataA.to_csv(test_dataA_result_path,
                       sep='\t',
                       index=None,
                       encoding='utf8'
                       )
    # print test_dataA.shape
    logging.debug('保存完成！')

def main_processing_dataB():
    train_dataB_file_path = '/home/jdwang/PycharmProjects/weiboStanceDetection/train_data/' \
                            'evasampledata4-TaskAR.txt'
    train_dataB = pd.read_csv(train_dataB_file_path,
                              sep='\t',
                              header=0)
    logging.debug('show the detail of task B')
    data_detail(train_dataB)
    # train_dataB = clean_data(train_dataB)

if __name__ =='__main__':

    main_processing_dataA()
