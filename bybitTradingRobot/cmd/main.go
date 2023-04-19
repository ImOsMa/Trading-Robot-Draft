package main

import (
	"fmt"

	"bybit-trading/pkg/client/bybit"
)

func main() {
	client := bybit.NewTestClient().WithAuth("fVaD7nHpwkWXsPGSrQ", "ifWp43Q2XpFSISwYvKyzRO1xcBHKGQbAp2a6")
	res, err := client.Spot().V1().SpotGetWalletBalance()
	if err != nil {
		fmt.Errorf("error")
	}
	fmt.Println(res.Result.Balances)

	//req := bybit.SpotPostOrderParam{
	//	Symbol: bybit.SymbolSpotETHUSDT,
	//	Qty:    1,
	//	Side:   bybit.SideBuy,
	//	Type:   bybit.OrderTypeSpotMarket,
	//}
	//resSpot, err := client.Spot().V1().SpotPostOrder(req)
	//if err != nil {
	//	fmt.Errorf("error")
	//}
	//fmt.Println(resSpot.Result)
}
