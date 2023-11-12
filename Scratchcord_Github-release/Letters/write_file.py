with open('all_letters.txt','w') as file:
    [file.write(chr(i)+'\n') for i in range(33,127)]