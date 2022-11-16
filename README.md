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
  
![image](https://user-images.githubusercontent.com/39136856/202146440-3dd056f4-446b-4ba5-9d6f-6ea617a08562.png)
   
  
## Moduł zrozumienia języka:
Moduł zrozumienia języka pozwala na ekstrakcję najważniejszych informacji zawartych w zdaniu wprowadzonym przez użytkownika. Rolą tego modułu jest wyznaczenie, które informacje w zdaniu opisują typy dokumentów lub klucze które powinien on zawierać.
  
Schemat modułu zrozumienia języka:
  
![image](https://user-images.githubusercontent.com/39136856/202146834-a6008bac-2bff-4fb8-a0cc-34ee692b8b6d.png)

Proces ekstrakcji informacji rozpoczyna się po otrzymaniu wiadomości od użytkownika. Pierwszym etapem jest wykorzystanie SpaCy w celu tokenizacji otrzymanego zdania. Każdy token następnie jest wektoryzowany oraz lematyzowany z wykorzystaniem tablic dołączanych do modelu SpaCy. Następnie zwektoryzowany tekst zostaje przekazany do funkcji obsługującej słowa OOV która uzupełnia wektory dla słów spoza słownika SpaCy. Przygotowane w ten sposób wektory przekazywane są do modelu Slot filler który znajduje na ich podstawie wyrażenia określające typy dokumentów, słowa klucze oraz spójniki występujące w zdaniu. Otrzymane sloty zostają następnie przekazane do funkcji poprawy słów która dla każdego wykrytego w zdaniu typu dokumentu przypisuje jego poprawną wersję z wykorzystaniem przygotowanej tablicy dokumentów. W ten sam sposób poprawiane są także spójniki którym dodatkowo przypisywana jest także operacja logiczna zdefiniowana w tablicy opratorów. Po wykonaniu wszystkich operacji moduł zwraca poprawione zdanie wraz z odpowiednio przypisanymi informacjami dodatkowymi, sloty oraz leksemy.
  
Schemat sieci MIMIC-RNN:  
   
![image](https://user-images.githubusercontent.com/39136856/202147322-560baace-d512-4374-9d17-55f45f236899.png)
  
  
Schemat sieci slot-fillera:  
  
![image](https://user-images.githubusercontent.com/39136856/201992688-78c4b9e7-0b8e-485c-9926-9615aa52df40.png)
  
  
## Genarator pytań
W celu utworzenia bazy treningowej do modelu slot fillera stworzony został program pozwalający na generowanie przykładowych zapytań oraz żądań dotyczących polecenia lub znalezienia dokumentu zawierającego dane klucze. Program ten oprócz wygenerowanego automatycznie zapytania zwracał także odpowiadającą mu tokenizacje oraz wektor odpowiednich slotów. Przyjęta podstawowa budowa zapytania przedstawia się następująco:  
  
[Początek polecenia][część dokumentowa][orzeczenie][część kluczowa]
  
Program polegał na odpowiednim wyborze każdej z części zapytania w kolejności od początku polecenia do części kluczowej z uwzględnieniem odpowiedniej akomodacji syntaktycznej między każdą z części.

  
Przedstawienie procesu dopasowywania części dokumentowej do początku zapytania:  
  
![image](https://user-images.githubusercontent.com/39136856/202148353-f850c0f3-d5cd-4e8d-b3a7-b4029af2d1a7.png)
  
  
Przykład dołączenia członu nadrzędnego grupy syntatkycznej orzeczenia do części dokumentowej:  
  
  ![image](https://user-images.githubusercontent.com/39136856/202148620-9d63dacf-022e-463f-aaf6-1c209a39204d.png)
  
  
Algorytm dodawania wyrazów do orzeczenia:  
  
![image](https://user-images.githubusercontent.com/39136856/202148752-347ba975-dc0d-47fd-ad23-1b2b3d30c53b.png)

Przykładowe pytania:  
  
![image](https://user-images.githubusercontent.com/39136856/202148939-985d755b-3298-48e7-8021-378995802d0b.png)
  
  
## Menadżer logiki

Schemat menadżera logiki:
  
![image](https://user-images.githubusercontent.com/39136856/201992986-ec69ec78-348a-4192-835a-01a1fbc13c83.png)
  
  
## Dialog

Opcje po wstępnym znalezieniu wyników:  
![image](https://user-images.githubusercontent.com/39136856/201993776-a9eb70d5-969a-4b60-bd85-7d9bab04dca5.png)
  
  
Uproszczony schemat przebiegu rozmowy:  
![image](https://user-images.githubusercontent.com/39136856/201993836-2cfe0fd8-aa93-455b-afb8-8ab96aa7935a.png)
  
