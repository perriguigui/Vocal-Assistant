import os
import csv
import glob
import pydub
import epitran
import unidecode
import librosa
import librosa.display
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
from tensorflow.python.keras import metrics, optimizers, losses
from tensorflow.python.keras.models import Model, Sequential
from tensorflow.python.keras.layers import Conv1D, Dense, Flatten,Lambda, Dropout, MaxPooling1D,LSTM

def displayMffc(mfcc,text):
    plt.figure(figsize=(10, 4))
    librosa.display.specshow(mfcc, x_axis='time')
    plt.colorbar()
    plt.title(text)
    plt.tight_layout()
    plt.show()

def find_mp3_files(names,path):
  files=glob.glob(path+'*.mp3')
  print
  sounds=[]
  for file in files:
    buffer = file.replace(".mp3", ".wav")
    for name in names:
        pathcsv=path+name
        #print(pathcsv)
        #print(buffer)
        if(pathcsv==buffer):
            buffer = buffer.replace(".wav", ".mp3")
            sounds.append(buffer)
  print("il y a ",len(sounds),"fichier mp3")
  return np.array(sounds)

def mp3towav(names,path):
    files = find_mp3_files(names,path)
    for file in files:
        sound = pydub.AudioSegment.from_mp3(file)
        newFile=file.replace(".mp3", ".wav")
        #peut etre a mettre: ,bitrate='16k', parameters=["-acodec","pcm_u16le","-ac","1","-ar","8000"]
        sound.export(newFile, format="wav",bitrate='16k')
        os.remove(file)

def readcsv():
    with open("C:/Users/anto/Documents/deepLearning/Vocal_Assistant/data/dev.tsv" , encoding="utf8") as tsvfile:
        tsvreader = csv.reader(tsvfile, delimiter="\t")
        names=[]
        texts=[]
        for line in tsvreader: 
            buffer = line[1].replace("mp3", "wav")
            names.append(buffer)
            texts.append(line[2])
    print("nb de csv",len(names))
    return names,texts

def loadWav(names,path):
    wavFiles=[]
    names=names[1:]
    for file in names:
        file=path+file
        y, sr = librosa.load(file, sr=16000)
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40)
        wavFiles.append(mfccs)
    return wavFiles

def preProcessText(texts):
    textsplit=[]
    for text in texts:
        text = unidecode.unidecode(text)
        text = text.lower()
        text = text.replace("\"", "")
        text = text.replace("(", "")
        text = text.replace(")", "")
        text = text.replace("_", "")
        text = text.replace("ç", "c")
        text = text.replace("à", "a")
        text = text.replace("º", "")
        text = text.replace("=", "")
        text = text.replace("^", "")
        text = text.replace("{", "")
        text = text.replace("}", "")
        text = text.replace(";", ",")
        text = text.replace("|", "")

        textsplit.append(text.split())
    return textsplit

def text2phonemes(text):
    epi = epitran.Epitran('fra-Latn')
    ipa=epi.transliterate(text)
    print(ipa)
    test = epitran.Epitran('fra-Latn',rev=True)
    print(test.reverse_transliterate(ipa))
    



def createModel():
    model = Sequential()

    model.add(Conv1D(8, 9, strides=4, padding="same", activation="elu"))
    model.add(MaxPooling1D(pool_size=2, strides=2, padding="same"))

    model.add(LSTM(1, return_sequences=True))
    N=6
    model.add(Lambda(lambda x: x[:, -N:, :]))
    
    model.add(Flatten())
    model.add(Dropout(.6))
    model.add(Dense(1024, activation="elu"))
    model.add(Dropout(.3))
    model.add(Dense(1))

    #adamperso = optimizers.Adam(lr=0.000001)
    model.compile(loss="mean_squared_error", optimizer="adam")
    
    return model

def gen_batch(files,label_files, batch_size = 64):
    while True:          
        batch_input = []
        batch_output = [] 
        batch_x=[]
        batch_y=[]
        size = 0
        # Read in each input, perform preprocessing and get labels          
        for file, label_file in zip(files, label_files):
            batch_x += [ file ]
            batch_y += [ label_file ] 
            if(size>=batch_size):
               batch_input.append(batch_x)
               batch_output.append(batch_y)
               size=0
            size=size+1
        #batch_x = np.array( batch_input )
        #batch_y = np.array( batch_output )
        
        yield( batch_x, batch_y )

    


@tf.function
def train_step(inputs, targets):
    # permet de surveiller les opérations réalisé afin de calculer le gradient
    with tf.GradientTape() as tape:
        # fait une prediction
        predictions = model(inputs)
        print("rotations shape after creation model",targets)
        print("prediction shape after creation model",predictions)
        # calcul de l'erreur en fonction de la prediction et des targets
        loss = loss_object(targets, predictions)
        print("calcul loss",loss)
    # calcul du gradient en fonction du loss
    # trainable_variables est la lst des variable entrainable dans le model
    gradients = tape.gradient(loss, model.trainable_variables)
    print("calcul gradient")
    # changement des poids grace aux gradient
    optimizer.apply_gradients(zip(gradients, model.trainable_variables))
    print("etape optimizer")
    # ajout de notre loss a notre vecteur de stockage
    train_loss(loss)
    print("etape train loss")
    train_accuracy(targets, predictions)
    print("etape train accuracy")

@tf.function
def predict(inputs):
    # Make a prediction on all the batch
    predictions = model(inputs)
    return predictions


if __name__ == "__main__":
    pathFile="C:\\Users\\anto\\Documents\\deepLearning\\Vocal_Assistant\\data\\clips\\"
    #text2phonemes('hello')
    names,texts = readcsv()
    #mp3towav(names,pathFile)
    #reduce for dev
    names= names[:20]
    texts= texts[:20]
    mfccs=loadWav(names,pathFile)
    print("mfccs load")
    #displayMffc(mfccs[2],texts[2])
    texts = preProcessText(texts)
    test = np.array(mfccs[2])
    print(test.shape)
    print(texts[2],mfccs[2])
    
    loss_object = tf.keras.losses.SparseCategoricalCrossentropy()
    optimizer = tf.keras.optimizers.Adam(lr=0.001)
    #track the evolution
    # Loss
    train_loss = metrics.Mean(name='train_loss')
    valid_loss = metrics.Mean(name='valid_loss')
    # Accuracy
    train_accuracy = metrics.SparseCategoricalCrossentropy(name='train_accuracy')
    valid_accuracy = metrics.SparseCategoricalCrossentropy(name='valid_accuracy')
    
    model = createModel()
    

    epochs = 20
    batch_size = 16

    model.reset_states()
    batch_inputs, batch_targets = next(gen_batch(mfccs, texts, batch_size))

    for epoch in range(epochs):
        for batch_inputs, batch_targets in gen_batch(mfccs, texts, batch_size):
            train_step(batch_inputs, batch_targets)
        template = '\r Epoch {}, Train Loss: {}, Train Accuracy: {}'
        print(template.format(epoch, train_loss.result(), train_accuracy.result()*100), end="")
        model.reset_states()