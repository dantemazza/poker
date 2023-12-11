import json
import csv
import re
import copy
import matplotlib.pyplot as plt

def main(full_log_path, ledger_path):
    players = set()
    transactions = {}
    stack_sizes = {}
    with open(ledger_path, 'r') as csv_file:  
        csv_reader = csv.reader(csv_file)
        next(csv_reader)
        for row in csv_reader:
            players.add(row[0])
    players = list(players)
    for player in players:
        transactions[player] = []
        stack_sizes[player] = []
    
    with open(full_log_path, 'r') as csv_file:
        hand_number = 0
        
        csv_reader = csv.reader(csv_file)
        for row in reversed(list(csv_reader)):
            if row and row[0].startswith('-- starting'):
                hand_number += 1
                for name, quantity in transactions.items():
                    if not quantity:
                        transactions[name].append(0)
                    elif len(quantity) != hand_number:
                        if len(quantity) > hand_number:
                            raise AssertionError()
                        transactions[name].append(transactions[name][-1])
            if row and row[0].startswith('Player stacks:'):
                stack_sizes = extract_stack_sizes(row[0], stack_sizes, copy.deepcopy(players))
            if row and (row[0].startswith('The admin updated') or 'joined the' in row[0] or 'quits the' in row[0]):
                transactions = extract_transactions(row[0], transactions)
    
    with open("transactions.json", "w") as f:
        json.dump(transactions, f, indent=2)
    with open("stack_sizes.json", "w") as f:
        json.dump(stack_sizes, f)
    

    hands = len(stack_sizes[next(iter(stack_sizes))])
    profits = {}
    for player, values in transactions.items():
        profits[player] = []
        stack_values = stack_sizes[player]
        for stack_size, transaction in zip(stack_values, values):
            profits[player].append(float(stack_size)-transaction)
    with open("profits.json", "w") as f:
        json.dump(profits, f)
    x = list(range(hands))
    for user, values in profits.items():
        numeric_values = [float(val) if isinstance(val, str) and val.replace(".", "", 1).isdigit() else 0 for val in values]
        plt.plot(numeric_values, label=user)
    plt.xlabel("Hand number")
    plt.ylabel("Stack Size $")
    plt.legend()
    plt.show()

def extract_transactions(row, transactions):
    name, quantity = extract_transaction(row)
    if not transactions[name]:
        transactions[name].append(quantity)
    else:
        transactions[name].append(quantity+transactions[name][-1])
    return transactions

def extract_transaction(input_string):
    player, quantity = None, None 
    if input_string.startswith('The admin updated'):
        player, quantity = extract_update(input_string)
    elif 'joined the' in input_string:
        print(player, quantity)
        player, quantity = extract_info(input_string, 'joined')
    elif 'quits the' in input_string:
        player, quantity = extract_info(input_string, 'quits')
        quantity *= -1
    return player, quantity

def extract_update(input_string):
    pattern = r'The admin updated the player "([^@"]+)(?: @ [^"]+)?" stack from (\d+\.\d{2}) to (\d+\.\d{2})'
    match = re.search(pattern, input_string)
    if match:
        player_name = match.group(1)
        old_value = match.group(2)
        updated_value = match.group(3)
        return player_name, float(updated_value)-float(old_value)
    else:
        raise AssertionError()

def extract_info(input_string):
    player = input_string.split(" @ ")[0].split('"')[-1]
    quantity = float(input_string.split(" ")[-1][:-1])
    return player, quantity

def extract_stack_sizes(row, stack_sizes, players):
    inputs = row.split('|')
    player_stacks = []
    for i in inputs:
        name, stack_size = extract_stack_size(i)
        players.remove(name)
        stack_sizes[name].append(stack_size)
    
    for player in players:
        stack_sizes[player].append(0)
    return stack_sizes       

def extract_stack_size(input_string):
    pattern =  r'#\d+ "(.*?) @ [^"]+" \((\d+\.\d+)\)'
    match = re.search(pattern, input_string)

    if match:
        name = match.group(1)
        number = match.group(2)
        return name, number
    else:
        raise AssertionError()

if __name__ == '__main__':
    main('full_log.csv', 'ledger.csv') 
