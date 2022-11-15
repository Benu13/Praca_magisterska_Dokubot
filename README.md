# Dokubot
Chatbot for intelligent document searching in polish language. 
  
## Goal  
The purpose of the work is to create a chatbot system that allows intelligent search of documents. The chatbot should understand the user's commands and respond accordingly.   It was assumed that, receiving a sentence containing requirements from the user, the bot should correctly extract the words that have meaning in the statement. In addition to 
this information, the bot should also understand the logic contained in the received command. Using the information extracted from the sentence about the type and content of the document being sought, the chatbot should search for the document or documents that most closely match the user's requirements.  
Communication should also include attempts to work with the user to resolve problems and ambiguities in the message received from him. Program should include a mechanism for asking the user relevant questions aimed at clarify requirements. In addition to understanding and searching, the chatbot should actively offer the ability to help narrow the search and rank the results according to their fit with the requirements. Communication should take place over the Internet and be conducted in Polish. 

## Files  
This repository contains all files used for creation of document recommending chatbot. This includes:  
-> Python code for chatbot  
-> Code for data acquisition  
-> Code for data preprocessing  
-> Code for database creation  
-> Code for creating questions for model training  

Creation and training of networks was done using GoogleColab (Files in repo are not valid):  
https://colab.research.google.com/drive/1z6WoUWEg6kNRVPlmXfZxiJT3Es31EVFs

# Opis (pl)

## Pozyskanie danych
Dokumenty pozyskano ze strony CEON.  

Pozyskane metadane:
-> Identyfikator  
-> Tytuł  
-> Autorzy  
-> Źródło  
-> Typ dokumentu  
-> Słowa kluczowe  
-> Adres URL  
  
Schemat pozyskania danych:  
  
![image](https://user-images.githubusercontent.com/39136856/201991862-d0726ba3-e6e9-4c76-b702-d42fd108b3ac.png)
  
  
## Budowa czatbota:  
  
![image](https://user-images.githubusercontent.com/39136856/201992061-b03ae557-c7ca-46c1-9fb8-76b4273c1f81.png)
  
  
## Moduł zrozumienia języka:
Schemat modułu zrozumienia języka:
  
![image](https://user-images.githubusercontent.com/39136856/201992369-c27c15a0-7730-475b-9662-a3ef33d86666.png)
  
 Schemat sieci MIMIC-RNN:  
   
 ![image](https://user-images.githubusercontent.com/39136856/201992615-129414f0-b09a-481d-a02d-363d244fba70.png)
  
  
Schemat sieci slot-fillera:  
  
![image](https://user-images.githubusercontent.com/39136856/201992688-78c4b9e7-0b8e-485c-9926-9615aa52df40.png)
  
  
## Genarator pytań

## Menadżer logiki

Schemat menadżera logiki:
  
![image](https://user-images.githubusercontent.com/39136856/201992986-ec69ec78-348a-4192-835a-01a1fbc13c83.png)
  
  
## Dialog

Opcje po wstępnym znalezieniu wyników:  
![image](https://user-images.githubusercontent.com/39136856/201993776-a9eb70d5-969a-4b60-bd85-7d9bab04dca5.png)
  
  
Uproszczony schemat przebiegu rozmowy:  
![image](https://user-images.githubusercontent.com/39136856/201993836-2cfe0fd8-aa93-455b-afb8-8ab96aa7935a.png)
  
  
## Odpowiedzi
  
