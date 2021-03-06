import glob
import numpy as np
import os
import pydub
from os import path
import customCsv 



def mp3towav(names,path):
    for name in names:
        pathName = path+name

        if(os.path.exists(pathName)):   
            sound = pydub.AudioSegment.from_mp3(pathName)
            newFile=pathName.replace(".mp3", ".wav")
            #peut etre a mettre: ,bitrate='16k', parameters=["-acodec","pcm_u16le","-ac","1","-ar","8000"]
            sound.export(newFile, format="wav",bitrate='16k')
            os.remove(pathName)
        
def delete_unused_files():
    os.chdir(pathFileV2)
    files=glob.glob('*.mp3')
    print("il y en a: ", len(files)," a suprimer.")
    for file in files:
        os.remove(file)


#exemple of use

if __name__ == "__main__":
    pathFile ="C:\\Users\\anto\\Documents\\deepLearning\\Vocal_Assistant\\data\\clips\\"
    pathFileV2 ="C:\\Users\\tompe\\Documents\\deepLearning\\Vocal_Assistant\\data\\clips\\"
    pathCsv = "C:/Users/anto/Documents/deepLearning/Vocal_Assistant/data/dev.tsv"
    pathCsvV2 = "C:/Users/tompe/Documents/deepLearning/Vocal_Assistant/data/dev.tsv"
    #va récuperer toutes les informations du csv concernant le nom du song et son texte
    SongCsv = customCsv.customCsv(pathCsvV2)
    SongCsv.readcsv()
    names,texts = SongCsv.getContent() 

    print("exemple: ",names[1]) 
    #va checker si le fichier exister et le convertir en mp3
    mp3towav(names,pathFileV2)
    #va supprimer tout les fichier mp3 qu'il reste 
    delete_unused_files()
