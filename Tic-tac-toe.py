from random import randint

def game(pole):
    print('Игра Крестики-Нолики')
    print(f'\n \ y |     |     |     |\n x \ |  1  |  2  |  3  |\n____\|_____|_____|_____|\n{'     |'*4}\n  1  |  {pole[0]}  |  {pole[1]}  |  {pole[2]}  |    \n{'_____|'*4}\n{'     |'*4}\n  2  |  {pole[3]}  |  {pole[4]}  |  {pole[5]}  |\n{'_____|'*4}\n{'     |'*4}\n  3  |  {pole[6]}  |  {pole[7]}  |  {pole[8]}  |\n{'_____|'*4}\n')
    sign='X' if randint(0,1)==1 else 'O'
    round_tf=True
    pole=list(pole)
    while round_tf:
        win_test=[]
        print('Xoд', sign)
        
        t_xy=True # I N P U T
        while t_xy:
            coords=input(' xy: ')
            if  pole[3*int(coords[0])-4+int(coords[1])]==' ':
                pole[3*int(coords[0])-4+int(coords[1])]=sign
                t_xy=False
            else:
                print("Клетка уже занята!")
                coords=input(' xy: ')
                      
        print(f'\n \ y |     |     |     |\n x \ |  1  |  2  |  3  |\n____\|_____|_____|_____|\n{'     |'*4}\n  1  |  {pole[0]}  |  {pole[1]}  |  {pole[2]}  |    \n{'_____|'*4}\n{'     |'*4}\n  2  |  {pole[3]}  |  {pole[4]}  |  {pole[5]}  |\n{'_____|'*4}\n{'     |'*4}\n  3  |  {pole[6]}  |  {pole[7]}  |  {pole[8]}  |\n{'_____|'*4}\n')
        win_test.append(pole[0]==pole[1]==pole[2]==sign)
        win_test.append(pole[3]==pole[4]==pole[5]==sign)
        win_test.append(pole[6]==pole[7]==pole[8]==sign)
        win_test.append(pole[0]==pole[3]==pole[6]==sign)
        win_test.append(pole[1]==pole[4]==pole[7]==sign)
        win_test.append(pole[2]==pole[5]==pole[8]==sign)
        win_test.append(pole[0]==pole[4]==pole[8]==sign)
        win_test.append(pole[2]==pole[4]==pole[6]==sign)
        if True in win_test:
            round_tf=False
            print(sign, 'победили!\n\n')
        sign='O' if sign=='X' else 'X'
        

pole=' '*9
game(pole)