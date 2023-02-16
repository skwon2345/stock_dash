from datetime import datetime
from pprint import pprint
from time import gmtime, mktime

import finnhub
import plotly.graph_objects as go


class Chart:
    def __init__(self, symbol, resolution, start_date, end_date):
        self.f = finnhub.Client(
            api_key="cdfl83iad3i8a4q95080cdfl83iad3i8a4q9508g"
        )

        self.symbol = symbol
        self.resolution = resolution

        self.start_date = start_date
        self.end_date = end_date

        self.start_timestamp = self._to_timestamp(self.start_date)
        self.end_timestamp = self._to_timestamp(self.end_date)

        self.uptrend = []
        self.downtrend = []

        self.vertices = []

        self.data = self._process(self.symbol)

        self.f.indices_const()

    def _to_timestamp(self, date: str) -> int:
        return int(
            datetime.timestamp(datetime.strptime(date, "%Y-%m-%d %H:%M:%S"))
        )

    def _format(self, dx):
        cnt = 0
        arr_calc = []
        arr_candle = []
        dataxxx = []
        for i in range(len(dx["c"])):
            arr_calc.append({})
            arr_candle.append(
                {
                    "Open": float(dx.get("o", 0.0)[i]),
                    "High": float(dx.get("h", 0.0)[i]),
                    "Low": float(dx.get("l", 0.0)[i]),
                    "Close": float(dx.get("c", 0.0)[i]),
                }
            )
            my_data = {
                "Date": datetime.fromtimestamp(
                    mktime(gmtime(dx.get("t")[i]))
                ).strftime("%Y-%m-%d %H:%M:%S"),
                "Time": dx.get("t")[i],
                # "Volume": float(dx_data.get("volume")),
                "Candle": arr_candle[cnt],
                "i": cnt,
                "calculations": arr_calc[cnt],
            }
            if dx.get("rsi") != None:
                my_data["calculations"]["RSI"] = dx.get("rsi")[i]
            dataxxx.append(my_data)
            cnt = cnt + 1

        return dataxxx

    def _arrange_high_low_list(self, high_list: list, low_list: list) -> list:
        high_i = 0
        low_i = 0
        ret = []
        trend = ""

        while high_i < len(high_list) and low_i < len(low_list):
            cur_high = high_list[high_i]
            cur_low = low_list[low_i]
            if cur_high[0] < cur_low[0]:
                if trend == "":
                    ret.append(cur_high)
                else:
                    if trend == "downtrend":
                        if ret[-1][1] < cur_high[1]:
                            ret[-1] = cur_high
                    else:
                        ret.append(cur_high)
                trend = "downtrend"
                high_i += 1

            elif cur_low[0] < cur_high[0]:
                if trend == "":
                    ret.append(cur_low)
                else:
                    if trend == "uptrend":
                        if ret[-1][1] > cur_low[1]:
                            ret[-1] = cur_low
                    else:
                        ret.append(cur_low)
                trend = "uptrend"
                low_i += 1

            else:
                if trend == "uptrend":
                    if ret[-1][1] > cur_low[1]:
                        ret[-1] = cur_low
                    else:
                        ret.append(cur_high)
                        trend = "downtrend"
                else:
                    if ret[-1][1] < cur_high[1]:
                        ret[-1] = cur_high
                    else:
                        ret.append(cur_low)
                        trend = "uptrend"
                high_i += 1
                low_i += 1

        last_element = -1.0
        if high_i < len(high_list):
            last_element = max(high_list[high_i:], key=lambda x: x[1])
            ret.append(last_element)
        elif low_i < len(low_list):
            last_element = max(low_list[low_i:], key=lambda x: x[1])
            ret.append(last_element)

        return ret

    def _get_trend_list(self, data: list, window: int) -> dict:
        i = 0

        high_list = []
        low_list = []

        while i < len(data):
            if i < window - 1:
                i += 1
                continue
            di = data[i]
            high_point = (di["Date"], di["Candle"]["High"])
            low_point = (di["Date"], di["Candle"]["Low"])

            for j in range(i, i - window, -1):
                dj = data[j]
                if dj["Candle"]["High"] > high_point[1]:
                    high_point = (dj["Date"], dj["Candle"]["High"])
                if dj["Candle"]["Low"] < low_point[1]:
                    low_point = (dj["Date"], dj["Candle"]["Low"])

            if len(high_list) > 0:
                if high_list[-1][1] != high_point[1]:
                    high_list.append(high_point)
            else:
                high_list.append(high_point)

            if len(low_list) > 0:
                if low_list[-1][1] != low_point[1]:
                    low_list.append(low_point)
            else:
                low_list.append(low_point)

            i += window - 1

        trend_list = self._arrange_high_low_list(high_list, low_list)

        return trend_list

    def _set_trend_list(self, trend_list: list) -> None:
        uptrend = []
        downtrend = []

        for i in range(len(trend_list) - 1):
            if trend_list[i][1] > trend_list[i + 1][1]:
                downtrend.append(dict([trend_list[i], trend_list[i + 1]]))
                self.vertices.append(trend_list[i])
                self.vertices.append(trend_list[i + 1])
            else:
                uptrend.append(dict([trend_list[i], trend_list[i + 1]]))
                self.vertices.append(trend_list[i])
                self.vertices.append(trend_list[i + 1])

        self.vertices = [*set(self.vertices)]

        self.uptrend = uptrend
        self.downtrend = downtrend

    def set_trend(self, window: int) -> None:
        trend_list = self._get_trend_list(self.data, window)
        self._set_trend_list(trend_list)

        for d in self.data:
            if d.get("trend"):
                del d["trend"]
            for up in self.uptrend:
                uptrend_date_list = list(up.keys())
                if (
                    d["Date"] > uptrend_date_list[0]
                    and d["Date"] <= uptrend_date_list[1]
                ):
                    d["trend"] = "uptrend"
                    break

            if d.get("trend") is None:
                for down in self.downtrend:
                    downtrend_date_list = list(down.keys())
                    if (
                        d["Date"] > downtrend_date_list[0]
                        and d["Date"] <= downtrend_date_list[1]
                    ):
                        d["trend"] = "downtrend"
                        break

            if d.get("trend") is None:
                d["trend"] = "undefined"

    def _calc_fib_retr(self) -> list:
        def getFibRET(start, end):
            start_price = start[1]
            end_price = end[1]

            diff = start_price - end_price
            return {
                "start": start,
                "end": end,
                "fib": {
                    "-1.618": end_price + (diff * -1.618),
                    "-1.382": end_price + (diff * -1.382),
                    "-1.236": end_price + (diff * -1.236),
                    "-0.886": end_price + (diff * -0.886),
                    "-0.786": end_price + (diff * -0.786),
                    "-0.618": end_price + (diff * -0.618),
                    "-0.5": end_price + (diff * -0.5),
                    "-0.382": end_price + (diff * -0.382),
                    "-0.236": end_price + (diff * -0.236),
                    # "0": l,
                    "0.236": end_price + (diff * 0.236),
                    "0.382": end_price + (diff * 0.382),
                    "0.5": end_price + (diff * 0.5),
                    "0.618": end_price + (diff * 0.618),
                    "0.786": end_price + (diff * 0.786),
                    "0.886": end_price + (diff * 0.886),
                    "1.236": end_price + (diff * 1.236),
                    "1.382": end_price + (diff * 1.382),
                    "1.618": end_price + (diff * 1.618),
                },
            }

        ret = []
        for i in range(len(self.vertices)):
            for j in range(len(self.vertices)):
                if j <= i:
                    continue
                if (
                    abs(self.vertices[i][1] - self.vertices[j][1])
                    / max([self.vertices[i][1], self.vertices[j][1]])
                ) > 0.3:
                    ret.append(getFibRET(self.vertices[i], self.vertices[j]))
        return ret

    def _count_overlapping(self, fib_list: list):
        def is_overlapped(p1: float, p2: float) -> bool:
            return (abs(p1 - p2) / max([p1, p2])) < 0.003

        for fib_dict in fib_list:
            fib = fib_dict["fib"]
            fib_values = list(fib.values())
            count = 0
            for vertex in self.vertices:
                for fib_value in fib_values:
                    if is_overlapped(fib_value, vertex[1]):
                        count += 1

            fib_dict["overlap_cnt"] = count

    def _process(self, symbol: str) -> list:
        data = self.f.technical_indicator(
            symbol=symbol,
            resolution=self.resolution,
            _from=self.start_timestamp,
            to=self.end_timestamp,
            indicator="rsi",
            indicator_fields={"timeperiod": 14},
        )

        data = self._format(data)

        return data

    def get_chart(self, trend: bool = False, window: int = 20) -> go.Figure():
        date = []
        open = []
        high = []
        low = []
        close = []

        for data in self.data:
            date.append(data["Date"])
            open.append(data["Candle"]["Open"])
            high.append(data["Candle"]["High"])
            low.append(data["Candle"]["Low"])
            close.append(data["Candle"]["Close"])

        fig = go.Figure(
            data=[
                go.Candlestick(
                    x=date,
                    open=open,
                    high=high,
                    low=low,
                    close=close,
                    showlegend=False,
                )
            ],
        )

        fig.update_layout(
            title=dict(
                text=f"<b>{self.symbol}</b>",
                x=0.5,
                y=0.95,
                font=dict(family="Arial", size=20, color="#000000"),
            ),
            xaxis_title="<b>Date</b>",
            yaxis_title="<b>Price ($)</b>",
            font=dict(
                family="Courier New, Monospace", size=12, color="#000000"
            ),
        )

        if not trend:
            return fig
        else:
            self.set_trend(window=window)
            a = self._calc_fib_retr()
            self._count_overlapping(a)
            if a:
                max_a = max(a, key=lambda x: x["overlap_cnt"])
                for k, v in list(max_a["fib"].items()):
                    fig.add_hline(
                        y=v,
                        annotation_text=f"{k} ({v})",
                        annotation_position="right",
                        # color="green",
                    )
            for uptrend in self.uptrend:
                fig.add_trace(
                    go.Scatter(
                        x=list(uptrend.keys()),
                        y=list(uptrend.values()),
                        mode="lines",
                        line=go.scatter.Line(color="green", width=2),
                        showlegend=False,
                    )
                )
            for downtrend in self.downtrend:
                fig.add_trace(
                    go.Scatter(
                        x=list(downtrend.keys()),
                        y=list(downtrend.values()),
                        mode="lines",
                        line=go.scatter.Line(color="red", width=2),
                        showlegend=False,
                    )
                )

            return fig
