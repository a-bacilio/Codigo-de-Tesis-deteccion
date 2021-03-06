#Este programa muestra el código para entrenar una red neuronal basado en 
#un modelo de Yann LeCun de los 90's pero con menos filtros

#Para empezar se carga las librerias necesarias de Keras, de Numpy y os
from keras.preprocessing.image import ImageDataGenerator
from keras.models import Model
from keras.models import Sequential
from keras.layers import Flatten
from keras.layers import Convolution2D
from keras.layers import Activation
from keras.layers import MaxPooling2D
from keras.layers import Dense
from keras.layers import Dropout
from keras.callbacks import ModelCheckpoint,Callback,ReduceLROnPlateau
import numpy as np
import os

#Ya que el código es casi el mismo para los 4 entrenamientos (solo varia el modelo
# ) se usa un nombre código
codename='yann_lecun_simple'

#Se declara la ubicacion de las imagenes que van a servir para el entrenamiento
data_dir='Data/'
train_data_dir = data_dir+'train/'
validation_data_dir = data_dir+'validation/'

#Esto declara la cantidad de imagenes que estan entrando para el entrenamineto
#y cuantas imagenes estan entrando para la validación
nb_train_samples = 7641
nb_validation_samples = 2374

#Esto declara el numero de epoch(ciclo de entrenamiento) inicial, sirve en 
#caso de que suceda una parada inesperada, el registro pueda continuar con el 
#numero de epoch que le corresponde
i_ep=0





#Esto declara el uso de un registro del learning rate, el cual es útil para ver
#cuantas veces se estanca el entrenamiento y si el entrenamiento avanza o no.
registro_lr=[]
class showlr(Callback):
    def on_train_begin(self, logs={}):
        registro_lr = np.load(codename +'.npy',[])
    def on_epoch_end(self, batch, logs={}):
        lr = self.model.optimizer.lr.get_value()
        registro_lr.append(lr)
        np.save(codename + '.npy',registro_lr)
        print(lr)




#Se declara el tamaño de la matríz de entrada para el entrenamiento del sistema
#en otras palabras el tamaño a la que la imagen entrante para que sirva de
#de material de entrenamiento  va a ser transformada
img_ancho, img_alto ,canales= 112, 112, 3

#A continuacion, se muestra el código del módelo a entrenar el cual usa 
#un modelo de Yann LeCun de los 90's pero con menos filtros

#####################################################
#INICIANDO NUEVO SISTEMA
######################################
#Se inicia el modulo con "Sequential"
model = Sequential()

#Ahora sigue una serie de filtros, activaciones Relu(que Yann LeCun no uso en
#ese entonces) y Subsamplings de matrices de 2x2
model.add(Convolution2D(8, 3, 3, input_shape=(3, 112, 112)))
model.add(Activation('relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))

model.add(Convolution2D(8, 3, 3))
model.add(Activation('relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))

model.add(Convolution2D(16, 3, 3))
model.add(Activation('relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))


#Se reduce todo a un solo valor que indique si es o no un cacao infectado
model.add(Flatten())
model.add(Dense(16))
model.add(Activation('relu'))
model.add(Dropout(0.5))
model.add(Dense(1))
model.add(Activation('sigmoid'))

#Se compila en el sistema Keras usando Theano o Tensorflow, ademas se define el
#elemento a minimizar para la optimización y las metricas a mostrar(precisión,
#loss,etc)
model.compile(loss='binary_crossentropy',
              optimizer='rmsprop',metrics=['accuracy'])


#################################################
#Esta parte del codigo permite reanudar el entrenamiento en caso de 
#accidentes
#
#path = 'modelos/'+codename+'/'
#name_list = os.listdir(path)
#full_list = [os.path.join(path,i) for i in name_list]
#tsl = sorted(full_list, key=os.path.getmtime)
#path_tsl=tsl[len(tsl)-1]
#i_ep=int(path_tsl[len(path_tsl)-35:len(path_tsl)-33])+1
#
#
#model = Sequential()
#model =load_model(path_tsl)

# Aca se declaran las transformaciones aleatorias que se van a dar a las imagenes 
#antes de usarlas para el entrenamiento, de esta manera se aumenta artificialmente
#la cantidad de imagenes para entrenar sin aumentar la base de datos de las
#imagenes
#rescale, dividimos el valor de cada pixel de las imagenes para que los valores
#de la imagen ahora vayan de 0 a 1. Esto ayuda a que los valores que se comunican
#entre las neuronas no sean grandes
#shear range, cizalladuras aleatorias de la imagen
#zoom range,  zoom aleatorio de hasta 0.2
#rotation range, rotaciones aleatorias de hasta 90 grados
#fill mode, copia los pixeles mas cercanos cuando al girar o hacer zoom quedan zonas
#vacias
#horizontal y vertical flip, voltear la imagen aleatoriamente de arriba a abajo o
#de derecha a izquierda
train_datagen = ImageDataGenerator(
        rescale=1./255,
        shear_range=0.2,
        zoom_range=0.2,
        rotation_range=90.,
		fill_mode='nearest',
        horizontal_flip=True,
        vertical_flip=True)

#Para las imagenes que se van a usar en la validacion solo se reescala
test_datagen = ImageDataGenerator(rescale=1./255)

#Esto indica al programa de donde obtener las imagenes y en que porciones 
#tomarlo
train_generator = train_datagen.flow_from_directory(
        train_data_dir,
        target_size=(img_ancho, img_alto),
        batch_size=4,
        class_mode='binary')

validation_generator = test_datagen.flow_from_directory(
        validation_data_dir,
        target_size=(img_ancho, img_alto),
        batch_size=4,
        class_mode='binary')


#Ahora agregamos al entrenamiento caracteristicas útiles en el caso de
#accidentes y para realizar el registro del entrenamiento

#Esta es la dirección donde se guarda un modelo despues de entrenar cada ciclo
#y la funcion que la guarda
direccion='modelos/'+codename+'/weights.{epoch:04d}-{acc:.4f}-{loss:.4f}-{val_acc:.4f}-{val_loss:.4f}.hdf5'
checkpoint = ModelCheckpoint(direccion,
                             monitor='val_acc',
                             verbose=1,
                             save_best_only=False,
                             save_weights_only=False,
                             mode='max')

#Esta característica reduce el learning rate cada vez que se el loss no disminuye
reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.9,patience=1, verbose=1,  cooldown=0, min_lr=0)
#Esta característica llama a la función explicada anteriormente que almacena el valor del
#learning rate
histlr=showlr()

#Esta característica llma a las anteriores para agregarlos al entrenamiento
callbacks_list = [checkpoint,reduce_lr,histlr]


#Ahora se entrena el sistema. batch_size define el tamaño de  la porción de 
#que va a memoria ram para el entrenamiento. Asi va de porción en porción hasta 
#acabar un ciclo. nb_epoch, define el numero de ciclos de entrenamiento
#callbacks llama a las características adicionales
#verbose sirve para mostrar el proceso del entrenamiento en  el prompt de la linea
#de comandos.
#val y train es la data que se usa para la validacion y el entrenamiento
#respectivamente.
model.fit_generator(
        train_generator,
        samples_per_epoch=nb_train_samples,
        nb_epoch=1000,
        callbacks=callbacks_list,
        validation_data=validation_generator,
        nb_val_samples=nb_validation_samples,
        initial_epoch=i_ep)
