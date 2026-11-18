from flask import Flask, jsonify, render_template_string, request

import requests

import time
import threading
from datetime import datetime
app = Flask(__name__)

BASE = "https://api.india.delta.exchange"

SYMBOL = "BTCUSD"
def get_usd_inr():
    response = requests.get(
        "https://open.er-api.com/v6/latest/USD",
        timeout=10
    )
    response.raise_for_status()

    data = response.json()

    if data.get("result") != "success":
        raise ValueError("Exchange rate unavailable")

    return float(data["rates"]["INR"])
@app.route("/api/exchange-rate")
def exchange_rate():
    try:
        rate = get_usd_inr()
        return jsonify(usd_inr=rate)
    except Exception as e:
        return jsonify(error=str(e)), 502
HTML = """

<!DOCTYPE html>

<html>

<head>

<meta name="viewport" content="width=device-width, initial-scale=1">

<title>Delta BTC Assistant</title>

<style>

body {background:#101522;color:white;font-family:Arial;padding:20px}

.card {background:#202b3d;padding:20px;border-radius:14px;margin:15px 0}

.price {font-size:32px;color:#36d399}

button {padding:12px;border:0;border-radius:8px;background:#2563eb;color:white}

</style>

</head>

<body>

<h2>Delta BTC Assistant</h2>

<div class="card">

<p>BTC Live Price</p>

<div class="price" id="price">Loading...</div>

<p id="status">Connecting to Delta Exchange...</p>

</div>

<div class="card">

<h3>Market Analysis</h3>

<p>5 Minute: <span id="m5">Loading</span></p>

<p>15 Minute: <span id="m15">Loading</span></p>

<p>1 Hour: <span id="h1">Loading</span></p>

</div>

<div class="card">

<h3>Trading Mode</h3>

<p>Paper analysis only. Real orders are disabled.</p>

<button onclick="loadData()">Refresh Data</button>

</div>

<script>

async function loadData(){

 try {

  const r = await fetch('/api/market');

  const d = await r.json();

  if(!r.ok) throw new Error(d.error || 'API error');

  document.getElementById('price').innerText =

    '$' + Number(d.price).toLocaleString();

  document.getElementById('status').innerText =

    'Live data received from Delta Exchange';

  document.getElementById('m5').innerText = d.trends['5m'];

  document.getElementById('m15').innerText = d.trends['15m'];

  document.getElementById('h1').innerText = d.trends['1h'];

 } catch(e) {

  document.getElementById('status').innerText = 'Connection error: ' + e.message;

 }

}

loadData();

setInterval(loadData, 30000);

</script>
<div class="card">
<h2>💰 Paper Trading Dashboard</h2>

<p>Starting Balance: ₹5,000</p>

<p>USD to INR Rate:
<input id="fx" type="number" value="90">
</p>

<h3>Available Cash</h3>
<h2 id="cash">Loading...</h2>

<h3>BTC Holdings</h3>
<h2 id="btc">0</h2>

<h3>Portfolio Value</h3>
<h2 id="total">Loading...</h2>

<h3>Profit / Loss</h3>
<h2 id="pnl">₹0</h2>

<input id="qty" type="number"
placeholder="BTC Quantity" step="0.000001">

<br><br>

<button onclick="trade('buy')">BUY BTC</button>
<button onclick="trade('sell')">SELL BTC</button>

<h3>Trade History</h3>
<div id="history"></div>
</div>
<h3>Auto Paper Trading</h3>
<p id="autoStatus">Auto Trading: OFF</p>
<button onclick="toggleAuto(true)">START AUTO</button>
<button onclick="toggleAuto(false)">STOP AUTO</button>
<script>
async function loadPaper(){
 try{
  const r=await fetch('/api/paper');
  const d=await r.json();
  if(!r.ok) throw new Error('Paper data unavailable');

  const fxResponse=await fetch('/api/exchange-rate');
  const fxData=await fxResponse.json();

  if(!fxResponse.ok) throw new Error('Exchange rate unavailable');

  const fx=Number(fxData.usd_inr);

  const m=await fetch('/api/market');
  const market=await m.json();

  if(!m.ok) throw new Error('Market data unavailable');

  const price=Number(market.price)*fx;
  const total=Number(d.cash)+Number(d.btc)*price;
  const pnl=total-5000;

  document.getElementById('cash').innerText=
  '₹'+d.cash.toFixed(2);

  document.getElementById('btc').innerText=
  d.btc.toFixed(8);

  document.getElementById('total').innerText=
  '₹'+total.toFixed(2);

  document.getElementById('pnl').innerText=
  '₹'+pnl.toFixed(2);

  document.getElementById('history').innerHTML=
  d.trades.map(t=>
  `<p>${t.side.toUpperCase()} | ${t.quantity} BTC | ₹${t.price.toFixed(2)}</p>`
  ).join('');

 }catch(e){
  console.log(e);
 }
}

async function trade(side){
 try{
  const qty=Number(document.getElementById('qty').value);

  if(qty<=0){
   alert('Enter valid BTC quantity');
   return;
  }

  const fxResponse=await fetch('/api/exchange-rate');
  const fxData=await fxResponse.json();

  if(!fxResponse.ok){
   throw new Error('Exchange rate unavailable');
  }

  const fx=Number(fxData.usd_inr);

  const m=await fetch('/api/market');
  const market=await m.json();

  if(!m.ok){
   throw new Error('Market data unavailable');
  }

  const price=Number(market.price)*fx;

  const r=await fetch('/api/paper/trade',{
   method:'POST',
   headers:{'Content-Type':'application/json'},
   body:JSON.stringify({
    side:side,
    price:price,
    quantity:qty
   })
  });

  const d=await r.json();

  if(!r.ok){
   alert(d.error);
   return;
  }

  alert('Paper Trade Successful!');
  loadPaper();

 }catch(e){
  alert('Trading error: '+e.message);
 }
}
let autoTimer = null;
let autoBusy = false;

async function runAutoTick() {
    if (autoBusy) return;

    autoBusy = true;

    try {
        const r = await fetch('/api/auto/tick', {
            method: 'POST'
        });

        const d = await r.json();

        document.getElementById('autoStatus').innerText =
            'Auto Trading: ' + d.action +
            (d.error ? ' | ' + d.error : '');

        if (r.ok) {
            await loadPaper();
        }

    } catch (e) {
        document.getElementById('autoStatus').innerText =
            'Auto Error: ' + e.message;
    } finally {
        autoBusy = false;
    }
}

async function toggleAuto(enabled) {
    try {
        const r = await fetch('/api/auto', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({enabled: enabled})
        });

        if (!r.ok) throw new Error('Auto setting failed');

        if (autoTimer) {
            clearInterval(autoTimer);
            autoTimer = null;
        }

        if (enabled) {
            document.getElementById('autoStatus').innerText =
                'Auto Trading: ON';

            await runAutoTick();

            autoTimer = setInterval(runAutoTick, 60000);

        } else {
            document.getElementById('autoStatus').innerText =
                'Auto Trading: OFF';
        }

    } catch (e) {
        alert('Auto Trading Error: ' + e.message);
    }
}
loadPaper();
setInterval(loadPaper,30000);
</script>
</body>

</html>

"""

def get_candles(resolution):

    end = int(time.time())

    minutes = {"5m": 5, "15m": 15, "1h": 60}

    start = end - minutes[resolution] * 100 * 60

    response = requests.get(

        BASE + "/v2/history/candles",

        params={

            "resolution": resolution,

            "symbol": SYMBOL,

            "start": start,

            "end": end

        },

        timeout=15

    )

    response.raise_for_status()

    data = response.json()

    if not data.get("success"):

        raise ValueError("Delta candle API returned an error")

    candles=data["result"]
    candles = sorted(candles, key=lambda c: int(c["time"]))
    return candles

def get_trend(candles):

    closes = [float(c["close"]) for c in candles]

    if len(closes) < 21:
        return "Insufficient data"

    def ema(values, period):
        alpha = 2 / (period + 1)
        value = values[0]

        for x in values[1:]:
            value = alpha * x + (1-alpha) * value

        return value

    fast = ema(closes, 9)
    slow = ema(closes, 21)
    macd_line = ema(closes, 12) - ema(closes, 26)
    macd_values = [ema(closes[:i+1], 12) - ema(closes[:i+1], 26) for i in range(len(closes))]
    signal_line = ema(macd_values, 9)
    macd_histogram = macd_values[-1] - signal_line 
    changes = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    gains = [max(change, 0) for change in changes]
    losses = [max(-change, 0) for change in changes]

    avg_gain = sum(gains[-14:]) / 14
    avg_loss = sum(losses[-14:]) / 14

    if avg_loss == 0:
        rsi = 100 if avg_gain > 0 else 50
    else:
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

    if fast > slow and rsi < 70 and macd_histogram > 0:
        return "Bullish"

    if fast < slow and rsi > 30 and macd_histogram < 0:
        return "Bearish"

    return "Neutral"
def ema(values, period):
    if not values:
        return 0.0

    multiplier = 2 / (period + 1)
    result = float(values[0])

    for value in values[1:]:
        result = (float(value) * multiplier) + (result * (1 - multiplier))

    return result
def get_macd_data(candles):
    closes = [float(c["close"]) for c in candles]

    if len(closes) < 35:
        return {"status": "Insufficient Data"}

    macd_values = []

    for i in range(25, len(closes)):
        macd = (
            ema(closes[:i+1], 12)
            - ema(closes[:i+1], 26)
        )
        macd_values.append(macd)

    signal_values = [
        ema(macd_values[:i+1], 9)
        for i in range(len(macd_values))
    ]

    macd_now = macd_values[-1]
    signal_now = signal_values[-1]
    histogram = macd_now - signal_now

    if macd_now > signal_now:
        status = "Bullish"
    elif macd_now < signal_now:
        status = "Bearish"
    else:
        status = "Neutral"

    return {
        "macd": round(macd_now, 4),
        "signal": round(signal_now, 4),
        "histogram": round(histogram, 4),
        "status": status
    }
@app.route("/")

def home():

    return render_template_string(HTML)

@app.route("/api/market")

def market():

    try:

        ticker = requests.get(

            BASE + "/v2/tickers/" + SYMBOL,

            timeout=15

        )

        ticker.raise_for_status()

        result = ticker.json()["result"]

        price = result.get("close") or result.get("mark_price")

        if price is None:

            raise ValueError("Price unavailable")
        trends = {}
        macd = {}
        for tf in ["5m", "15m", "1h"]: 
            candles = get_candles(tf)
            trends[tf] = get_trend(candles)

            macd[tf] = get_macd_data(candles)

        return jsonify(
            price=price,
            trends=trends,
            macd=macd
        ) 
    except Exception as e:

        return jsonify(error=str(e)), 502
# PAPER TRADING SYSTEM
PAPER = {
    "cash": 5000.0,
    "btc": 0.0,
    "entry_price": 0.0,
    "stop_loss": 0.0,
    "trades": []
}

AUTO = {
    "enabled": False,
    "last_action": "HOLD",
    "last_check": None
}
@app.route("/api/auto", methods=["GET", "POST"])
def auto_control():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        enabled = data.get("enabled")

        if not isinstance(enabled, bool):
            return jsonify(error="Invalid setting"), 400

        AUTO["enabled"] = enabled

    return jsonify(AUTO)
@app.route("/api/paper", methods=["GET"])
def paper_status():
    with PAPER_LOCK:
        return jsonify(PAPER)
@app.route("/api/paper/trade", methods=["POST"])
def paper_trade():
    data = request.get_json(silent=True) or {}
    side = data.get("side")

    try:
        price = float(data.get("price", 0))
        quantity = float(data.get("quantity", 0))
    except (TypeError, ValueError):
        return jsonify(error="Invalid price or quantity"), 400

    if side not in ("buy", "sell"):
        return jsonify(error="Invalid trade type"), 400

    if price <= 0 or quantity <= 0:
        return jsonify(error="Invalid price or quantity"), 400

    with PAPER_LOCK:
        if side == "buy":
            cost = price * quantity

            if PAPER["btc"] > 0:
                return jsonify(error="Position already open"), 400

            if cost > 500:
                return jsonify(error="Maximum trade allocation is ₹500"), 400

            if cost > PAPER["cash"]:
                return jsonify(error="Insufficient balance"), 400

            PAPER["cash"] -= cost
            PAPER["btc"] += quantity
            PAPER["entry_price"] = price
            PAPER["stop_loss"] = price * 0.90

        else:
            if quantity > PAPER["btc"]:
                return jsonify(error="Insufficient BTC"), 400

            PAPER["cash"] += price * quantity
            PAPER["btc"] -= quantity

            if PAPER["btc"] == 0:
                PAPER["entry_price"] = 0.0
                PAPER["stop_loss"] = 0.0

        PAPER["trades"].append({
            "side": side,
            "price": price,
            "quantity": quantity
        })

        return jsonify(
            success=True,
            cash=PAPER["cash"],
            btc=PAPER["btc"],
            entry_price=PAPER["entry_price"],
            stop_loss=PAPER["stop_loss"],
            trades=PAPER["trades"]
        )


  # AUTOMATIC PAPER TRADING ENGINE

AUTO_LOCK = threading.Lock()
PAPER_LOCK = threading.Lock()
@app.route("/api/auto/tick", methods=["POST"])
def auto_tick():

    if not AUTO["enabled"]:
        return jsonify(action="HOLD", message="Auto Trading is OFF")

    with AUTO_LOCK:
        try:
            response = requests.get(
                BASE + "/v2/tickers/" + SYMBOL,
                timeout=15
            )
            response.raise_for_status()

            ticker_data = response.json()["result"]

            if isinstance(ticker_data, list):
                ticker_data = ticker_data[0]

            price_usd = float(
                ticker_data.get("close")
                or ticker_data.get("mark_price")
                or 0
            )

            if price_usd <= 0:
                raise ValueError("Invalid BTC price")

            price = price_usd * get_usd_inr()

            candles_5m = get_candles("5m")
            candles_15m = get_candles("15m")

            trend_5m = get_trend(candles_5m)
            trend_15m = get_trend(candles_15m)

            action = "HOLD"

            with PAPER_LOCK:

                if PAPER["btc"] > 0 and price <= PAPER["stop_loss"]:
                    action = "SELL"

                elif (
                    trend_5m == "Bearish"
                    and trend_15m == "Bearish"
                    and PAPER["btc"] > 0
                ):
                    action = "SELL"

                elif (
                    trend_5m == "Bullish"
                    and trend_15m == "Bullish"
                    and PAPER["btc"] == 0
                ):
                    action = "BUY"

                if action == "BUY":
                    cost = min(500.0, PAPER["cash"])

                    if cost > 0:
                        quantity = cost / price

                        PAPER["cash"] -= cost
                        PAPER["btc"] += quantity
                        PAPER["entry_price"] = price
                        PAPER["stop_loss"] = price * 0.90

                        PAPER["trades"].append({
                            "side": "buy",
                            "price": price,
                            "quantity": quantity
                        })
                    else:
                        action = "HOLD"

                elif action == "SELL":
                    quantity = PAPER["btc"]

                    if quantity > 0:
                        PAPER["cash"] += price * quantity
                        PAPER["btc"] = 0.0
                        PAPER["entry_price"] = 0.0
                        PAPER["stop_loss"] = 0.0

                        PAPER["trades"].append({
                            "side": "sell",
                            "price": price,
                            "quantity": quantity
                        })

                cash = PAPER["cash"]
                btc = PAPER["btc"]

            AUTO["last_action"] = action
            AUTO["last_check"] = datetime.now().isoformat()

            return jsonify(
                success=True,
                action=action,
                trend_5m=trend_5m,
                trend_15m=trend_15m,
                price_inr=price,
                cash=cash,
                btc=btc
            )

        except Exception as e:
            AUTO["last_action"] = "HOLD"

            return jsonify(
                success=False,
                action="HOLD",
                error=str(e)
            ), 502
if __name__ == "__main__":

    app.run(host="0.0.0.0", port=10000)
