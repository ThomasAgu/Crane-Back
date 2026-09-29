#tuplas son como vectores constantes, no se puede ageregar, eliminar, añadir y si sacamos un elemento creamos una nueva tupla
#lo que si es igual para preguntar si el elemento esta en la tupla
#tuplas sintaxis: 
nombreTupla = (1,2,3,"maicol Chakson")
print (nombreTupla[:])
#para convertir una tupla en lista
miLista = list(nombreTupla)
miLista.append("negro kbza")
print (miLista [:])
#metodo inverso
miLista2 = [1,2,3,4,5]
miTupla2 = tuple (miLista2)
print (miTupla2)
#para contar cuantas veces se encientra un elemento
print (miTupla2.count(4))
print (len(miLista2))
#para crear tuopla unitaria : 
unitaria = (5,)
#para desempaquetar una tupla bro rre flash
num1, num2, num3, num4, num5 = miTupla2