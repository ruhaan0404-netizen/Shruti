import os
import requests
import json
from bs4 import BeautifulSoup

def main():
    with open("specific_question.html","r",encoding="utf-8") as f:
        content = f.read()
        soup = BeautifulSoup(content,'lxml')
        soup.prettify()
        problem_part=soup.find("div",class_='problem-statement')
        contents = problem_part.get_text(separator="\n",strip=True)
        # print(contents)
        with open("question.txt","w",encoding="utf-8") as f:
            f.write(contents)
    
main()