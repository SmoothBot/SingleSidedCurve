from itertools import count
from brownie import Wei, reverts, Contract
import eth_abi
from brownie.convert import to_bytes
from useful_methods import genericStateOfStrat,genericStateOfVault
import random
import brownie

def strat_share_price(vault, strategy):
    debt = vault.strategies(strategy)['totalDebt']
    if (debt == 0):
        return 1
    return strategy.estimatedTotalAssets() / debt

def test_cusd3pool_usdc(whale, Strategy, strategy_usdc, accounts, cusd3poolyvault, chain, usdc_vault, gov, strategist, interface):
    strategist = gov
    vault = usdc_vault
    currency = interface.ERC20(vault.token())
    decimals = currency.decimals()
    gov = accounts.at(vault.governance(), force=True)
    strategy = strategy_usdc

    yvault = cusd3poolyvault
    #amount = 1000*1e6
    #amounts = [0, 0, amount]
    print("curveid: ", strategy.curveId())
    #print("slip: ", strategy._checkSlip(amount))
    #print("expectedOut: ", amount/strategy.virtualPriceToWant())
    print("curve token: ", strategy.curveToken())
    print("ytoken: ", strategy.yvToken())
    yvault.setDepositLimit(2 **256 -1 , {'from': yvault.governance()})
    #print("real: ", ibCurvePool.calc_token_amount(amounts, True))
    currency.approve(vault, 2 ** 256 - 1, {"from": whale})
    whale_before = currency.balanceOf(whale)
    print(currency.name())
    print (whale_before/1e6)
    whale_deposit = 30_000 * (10 ** (decimals))
    vault.deposit(whale_deposit, {"from": whale})
    vault.setManagementFee(0, {"from": gov})

    #idl = Strategy.at(vault.withdrawalQueue(1))
    #vault.updateStrategyDebtRatio(idl, 0 , {"from": gov})
    #debt_ratio = 2000
    #v0.3.0
    vault.addStrategy(strategy, 10000, 0, 2**256-1, 1000, {"from": gov})

    print('strat share: {}'.format(strat_share_price(vault, strategy)))
    strategy.setDoHealthCheck(False, {"from": gov})
    strategy.harvest({'from': strategist})
    print('strat share: {}'.format(strat_share_price(vault, strategy)))
    genericStateOfStrat(strategy, currency, vault)
    #genericStateOfStrat(strategy, currency, vault)
    #genericStateOfVault(vault, currency)
    print(yvault.pricePerShare()/1e6)

    # accrue returns on yvVault lp strat
    ibcrvStrat1 = Contract(yvault.withdrawalQueue(0))
    vGov = accounts.at(yvault.governance(), force=True)
    ibcrvStrat1.harvest({"from": vGov})
    chain.sleep(2016000)
    chain.mine(1)
    ibcrvStrat1.setDoHealthCheck(False, {"from": vGov})
    ibcrvStrat1.harvest({"from": vGov})
    chain.sleep(21600)
    chain.mine(1)

    # now harvest and get the returns in this strat
    print(yvault.pricePerShare()/1e6)
    strategy.harvest({'from': strategist})
    print(vault.strategies(strategy))
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)
    chain.sleep(21600)
    chain.mine(1)
 
    assert False
    vault.withdraw(vault.balanceOf(whale), whale, 200,{"from": whale})
    whale_after = currency.balanceOf(whale)
    profit = (whale_after - whale_before)
    print("profit =", profit/(10 ** (decimals)))
    assert profit > 0
    print("balance left =", vault.balanceOf(whale))
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)
    vault.updateStrategyDebtRatio(strategy, 0 , {"from": gov})
    strategy.setDoHealthCheck(False, {"from": gov})
    #chain.mine(1)

    strategy.harvest({'from': strategist})
    genericStateOfStrat(strategy, currency, vault)