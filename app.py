from re import L
import os
import json
import librosa
import matplotlib.pyplot as plt
import librosa.display
import seaborn as sns
from matplotlib import pyplot as plt
import numpy as np
from werkzeug.utils import secure_filename
from playsound import playsound
import soundfile as sf
from io import BytesIO
from flask import Flask, render_template, request


app = Flask(__name__)
UPLOAD_FOLDER = '/static/voice/reg'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/postmethod', methods = ['POST'])
def get_post_javascript_data():
        if request.method == 'POST':
                file = request.files['voice']
                name=file.filename
                if(os.path.isfile(secure_filename(name))):
                        file.save(secure_filename(name+"temp.wav"))
                        Input_base_autor = secure_filename(name)
                        Input_current_autor = secure_filename(name)+"temp.wav"
                        otvet = authorization(Input_base_autor, Input_current_autor)
                        if otvet==1:
                                print("YES")
                                return json.dumps({'success':True}), 200, {'ContentType':'application/json'} 
                        else: 
                                print("NO")
                                return json.dumps({'success':False}), 200, {'ContentType':'application/json'} 
                        
                else:
                        file.save(secure_filename(name))
        return json.dumps({'success':True}), 200, {'ContentType':'application/json'} 



def changing(matrix):
        arr = [elem for el in matrix for elem in el]
        return(arr)


def trimmer_base(wav): #Обрезает паузы и тишину для файла регистрации
        clips = librosa.effects.split(wav, top_db=20)
        wav_data = []
        for c in clips:
                    data = wav[c[0]: c[1]]
                    wav_data.extend(data)
        sf.write('base.wav', wav_data, 22050)

def trimmer_current(wav): #Обрезает паузы и тишину для файла текущей регистрации
        clips = librosa.effects.split(wav, top_db=20)
        wav_data = []
        for c in clips:
                    data = wav[c[0]: c[1]]
                    wav_data.extend(data)
        sf.write('current.wav', wav_data, 22050)

def authorization(base, current):
        yt1 , sft1 = librosa.load(current, sr=22050, mono=True, offset=0.0, res_type='kaiser_best') #Читаем файл
        yt2 , sft2 = librosa.load(base, sr=22050, mono=True, offset=0.0, res_type='kaiser_best')

        ytt1, index = librosa.effects.trim(yt1, top_db=20, frame_length=256, hop_length=64) #Отрезаем начало и конец с тишиной
        ytt2, index = librosa.effects.trim(yt2, top_db=20, frame_length=256, hop_length=64)

        trimmer_current(ytt1) 
        trimmer_base(ytt2)

        base_temp = 'base.wav'
        current_temp = 'current.wav' #Добавляем переменные обрезанными от тишины дорожками

        ytemp1 , sftemp1 = librosa.load(current_temp, sr=22050, mono=True, offset=0.0, res_type='kaiser_best') #Читаем файл для определения длительности
        ytemp2 , sftemp2 = librosa.load(base_temp, sr=22050, mono=True, offset=0.0, res_type='kaiser_best')
        
        dur1 = librosa.get_duration(y=ytemp1, sr=sftemp1) #Выясняем, какой длины после всех операций файлы
        dur2 = librosa.get_duration(y=ytemp2, sr=sftemp2)
        if dur1 < 3.0 or dur2 < 3.0:
            final = 0
            return final
        final_dur = min([dur1,dur2]) #По понятным причинам выбираем минимальный

        ytt1 , sf1 = librosa.load(current_temp, sr=22050, mono=True, offset=0.0, duration=final_dur, res_type='kaiser_best') #Читаем файл
        ytt2 , sf2 = librosa.load(base_temp, sr=22050, mono=True, offset=0.0, duration=final_dur, res_type='kaiser_best')
        
        y1_pp = librosa.effects.preemphasis(ytt1, coef=0.97, zi=None, return_zf=False) #Производим коррекцию искажений дорожки (результат: подрезаются низкие частоты)
        y2_pp = librosa.effects.preemphasis(ytt2, coef=0.97, zi=None, return_zf=False)

        fcc_current = librosa.feature.mfcc(y=y1_pp, sr=sf1, n_mfcc=12) #Вычисляем мел-кепстральные коэффициенты
        fcc_base = librosa.feature.mfcc(y=y2_pp, sr=sf2, n_mfcc=12)

        fcc_current_delta = librosa.feature.delta(fcc_current) #Вычисляем для MFCC дельта-функции 
        fcc_current_delta_array = changing(fcc_current_delta)

        fcc_base_delta = librosa.feature.delta(fcc_base) 
        fcc_base_delta_array = changing(fcc_base_delta) #матрицу преобразуем в массив

        fcc_current_delta_array_around = np.around(fcc_current_delta_array)
        fcc_base_delta_array_around = np.around(fcc_base_delta_array) #Округляем значения

        base = fcc_base_delta_array_around
        current = fcc_current_delta_array_around

        print('fcc_current_delta_array')
        print(current)
        print('')
        print('fcc_base_delta_array')
        print(base)

        error = 3 #Величина ошибки
        hit = 0
        if len(base)!=len(current): #Простейший алгоритм сравнивания
                print('Error')
        for i in range(len(base)):
                if current[i] - error <= base[i] <= current[i] + error:
                        hit+=1
        pin = hit/len(base)
        print(pin)

        final=0

        if pin > 0.5:
                final = 1
        else:
                final = 0
        #print(final)        
        return final






if __name__ == '__main__':
    app.run(debug=True, port=8080)
