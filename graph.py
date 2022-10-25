import os
import sys
import json
from statistics import mean

import matplotlib.pyplot as plt

def load_benchmark_file(port):
    filename = f'.{port}.benchmark.json'
    with open(filename) as f:
       data = json.load(f)
    return data

def fuzzy_get(json, k):
    key, = json.keys()
    if k in key:
        return json.get(key)
    else:
        return None

def swapToFunc(json):
    key, = json.keys()
    return key == 'swapToLowerSqrtPrice' or key == 'swapToHigherSqrtPrice'

def function_performance(file, function, benchmark, access_function):
    functions = benchmark[file] or []
    return [access_function(f, function) for f in functions if not swapToFunc(f) and fuzzy_get(f, function) != None ]

def pull_step_count(perf, function):
    execution_resouces = fuzzy_get(perf, function)
    return execution_resouces.get('n_steps') or\
        execution_resouces.get('execution_resources').get('n_steps')

def pull_gas_usage(perf, function):
    execution_resouces = fuzzy_get(perf, function)
    val = (execution_resouces.get('actual_fee') or 0)
    if val == 0:
        return 0

    gas_price = 100 * 10**9
    return  val // gas_price

def builtin_usage(prop):
    def extracter(perf, function):
        execution_resouces = fuzzy_get(perf, function)
        return execution_resouces.get('execution_resources').get("builtin_instance_counter").get(prop)

    return extracter

def graph(perf, function, title):
    x_min = min(perf)
    x_max = max(perf)
    filename = title.replace(" ", "_").lower()

    print(x_min, x_max)
    plt.figure(figsize=(10,7))
    plt.hist(perf,bins=250)
    plt.gca().set(title=f'{title} distribution for Warp\'d Uniswap v3 {function} function', ylabel='Frequency', xlabel=title);
    plt.savefig(f"{filename}_distribution.png")

def graph_eth_gas(perf, function):
    x_min = min(perf)
    x_max = max(perf)

    print(x_min, x_max)
    plt.figure(figsize=(10,7))
    plt.hist(perf,bins=250)
    plt.gca().set(title=f'Gas used distribution for EVM Uniswap v3 {function} function', ylabel='Frequency', xlabel='Gas used');
    plt.savefig("gas_swap.png")

def graph_gas_compared(eth_gas, stark_gas, function):
    plt.figure(figsize=(10,7))

    bins = 200
    plt.hist(eth_gas, color="r", alpha=0.5, bins=bins, label="Ethereum")
    plt.hist(stark_gas, color="blue", alpha=0.5, bins=bins, label="StarkNet")
    plt.legend(loc='best')
    plt.gca().set(title=f'Gas usage compared for Uniswap v3 {function} function', ylabel='Frequency', xlabel="Gas");
    plt.savefig("gas_compared.png")

if __name__ == "__main__":
    file, function, port = sys.argv[1:]

    gas = json.load(open('gas.json'))
    benchmark = load_benchmark_file(port)

    step_counts = function_performance(file, function, benchmark, pull_step_count)
    gas_fee = function_performance(file, function, benchmark, pull_gas_usage)
    range_checks = function_performance(file, function, benchmark, builtin_usage('range_check_builtin'))
    pedersens = function_performance(file, function, benchmark, builtin_usage('pedersen_builtin'))
    bitwises = function_performance(file, function, benchmark, builtin_usage('bitwise_builtin'))

    print(f'starknet len {len(gas_fee)}')
    print(f'ethereum len {len(gas)}')
    print(mean(gas)/ mean(gas_fee))

    graph_gas_compared(gas, gas_fee, function)
    graph(step_counts, function, "Step Count")
    graph(gas_fee, function, "Gas Usage")
    graph(pedersens, function, "Pedersen Builtin")
    graph(bitwises, function, "Bitwise Builtin")
    graph(range_checks, function, "Range check Builtin")
    graph_eth_gas(gas, 'swap')
