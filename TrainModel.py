#import SplitText
#import CleanText
from pickle import load
from numpy import array
from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences
from keras.utils import to_categorical
from keras.utils.vis_utils import plot_model
from keras.models import Sequential
from keras.layers import LSTM
from keras.layers import Dense
from keras.layers import Embedding
from keras.layers import RepeatVector
from keras.layers import TimeDistributed
from keras.callbacks import ModelCheckpoint


# load a clean dataset
def load_clean_sentences(filename):
    return load(open(filename, 'rb'))


# fit a tokenizer
def create_tokenizer(lines):
    tokenizer = Tokenizer()
    tokenizer.fit_on_texts(lines)
    return tokenizer


# max sentence length
def max_length(lines):
    return max(len(line.split()) for line in lines)


# encode and pad sequences
def encode_sequences(tokenizer, length, lines):
    # integer encode sequences
    X = tokenizer.texts_to_sequences(lines)
    # pad sequences with 0 values
    X = pad_sequences(X, maxlen=length, padding='post')
    return X


# one hot encode target sequence
def encode_output(sequences, vocab_size):
    ylist = list()
    for sequence in sequences:
        encoded = to_categorical(sequence, num_classes=vocab_size)
        ylist.append(encoded)
    y = array(ylist)
    y = y.reshape(sequences.shape[0], sequences.shape[1], vocab_size)
    return y


# defining the NMT model
def define_model(src_vocab, tar_vocab, src_timesteps, tar_timesteps, n_units):
    model = Sequential()
    model.add(Embedding(src_vocab, n_units, input_length=src_timesteps, mask_zero=True))
    model.add(LSTM(n_units))
    model.add(RepeatVector(tar_timesteps))
    model.add(LSTM(n_units, return_sequences=True))
    model.add(TimeDistributed(Dense(tar_vocab, activation='softmax')))
    return model


# load datasets
dataset = load_clean_sentences('yemba-english-both.pkl')
train = load_clean_sentences('yemba-english-train.pkl')
test = load_clean_sentences('yemba-english-test.pkl')

# preparing yemba tokenizer
yemba_tokenizer = create_tokenizer(dataset[:, 0])
yemba_vocab_size = len(yemba_tokenizer.word_index) + 1
yemba_length = max_length(dataset[:, 0])
print('Yemba Vocabulary Size: %d' % yemba_vocab_size)
print('Yemba Max Length: %d' % (yemba_length))
# preparing english tokenizer
eng_tokenizer = create_tokenizer(dataset[:, 1])
eng_vocab_size = len(eng_tokenizer.word_index) + 1
eng_length = max_length(dataset[:, 1])
print('English Vocabulary Size: %d' % eng_vocab_size)
print('English Max Length: %d' % (eng_length))

# prepare training data
trainX = encode_sequences(eng_tokenizer, eng_length, train[:, 1])
trainY = encode_sequences(yemba_tokenizer, yemba_length, train[:, 0])
trainY = encode_output(trainY, yemba_vocab_size)
# prepare validation data
testX = encode_sequences(eng_tokenizer, eng_length, test[:, 1])
testY = encode_sequences(yemba_tokenizer, yemba_length, test[:, 0])
testY = encode_output(testY, yemba_vocab_size)

# define model
model = define_model(eng_vocab_size, yemba_vocab_size, eng_length, yemba_length, 256)
model.compile(optimizer='adam', loss='categorical_crossentropy')
# summarize defined model
print(model.summary())
plot_model(model, to_file='model.png', show_shapes=True)
# fit model
filename = 'model.h5'
checkpoint = ModelCheckpoint(filename, monitor='val_loss', verbose=1, save_best_only=True, mode='min')
model.fit(trainX, trainY, epochs=30, batch_size=64, validation_data=(testX, testY), callbacks=[checkpoint], verbose=2)
