import os

pwd = os.path.dirname(__file__)

def account():
    with open(pwd+'/account.py') as f:
        account = f.readlines()
    account = map(lambda _:_.split(),account)
    restore_account = []
    for _ in account:
        restore_dict = {}
        restore_dict['username'] = _[0]
        restore_dict['password'] = _[1]
        restore_account.append(restore_dict)
    return restore_account

if __name__ == '__main__':
    account = account()
    print(account)

