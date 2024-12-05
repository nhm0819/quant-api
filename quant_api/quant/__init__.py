from typing import Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
import numpy as np


@dataclass
class Position:
    symbol: str
    size: float
    entry_price: float
    entry_time: datetime
    trade_id: str


@dataclass
class Order:
    symbol: str
    side: str  # 'BUY' or 'SELL'
    size: float
    order_type: str  # 'MARKET' or 'LIMIT'
    price: float = None


class MultiAssetCryptoStrategy:
    def __init__(
        self,
        symbols: List[str],
        leverage: float = 1.0,
        lookback_periods: Dict[str, int] = {
            "volume": 24,  # Hours for volume profile
            "volatility": 48,  # Hours for volatility calculation
            "correlation": 168,  # Hours for correlation calculation
            "momentum": 12,  # Hours for momentum signals
        },
        position_limits: Dict[str, float] = None,
        vol_window: int = 24,
        vol_threshold: float = 2.0,
        min_trade_volume: float = 1000000,  # Minimum USD volume
        max_correlation: float = 0.7,
        rsi_period: int = 14,
        rsi_thresholds: Tuple[float, float] = (30, 70),
    ):
        """
        Initialize the multi-asset cryptocurrency trading quant.

        Args:
            symbols: List of trading pairs (e.g., ['BTC-USDT', 'ETH-USDT'])
            leverage: Maximum leverage to use
            lookback_periods: Dictionary of lookback periods for different calculations
            position_limits: Maximum position size per symbol in USD
            vol_window: Window for volatility calculation in hours
            vol_threshold: Volatility threshold for position sizing
            min_trade_volume: Minimum 24h trading volume in USD
            max_correlation: Maximum allowed correlation between assets
            rsi_period: Period for RSI calculation
            rsi_thresholds: Tuple of (oversold, overbought) RSI levels
        """
        self.symbols = symbols
        self.leverage = leverage
        self.lookback_periods = lookback_periods
        self.position_limits = position_limits or {sym: 100000 for sym in symbols}
        self.vol_window = vol_window
        self.vol_threshold = vol_threshold
        self.min_trade_volume = min_trade_volume
        self.max_correlation = max_correlation
        self.rsi_period = rsi_period
        self.rsi_thresholds = rsi_thresholds

        # Strategy state
        self.positions: Dict[str, Position] = {}
        self.historical_positions: List[Position] = []
        self.pending_orders: List[Order] = []

        # Cache for computed metrics
        self._metric_cache = {}

    def calculate_volume_profile(
        self, trades_data: Dict[str, pd.DataFrame], klines_data: Dict[str, pd.DataFrame]
    ) -> Dict[str, pd.DataFrame]:
        """
        Calculate volume profile metrics using both trades and klines data.

        Args:
            trades_data: Dictionary of trades DataFrames per symbol
            klines_data: Dictionary of OHLCV DataFrames per symbol

        Returns:
            Dictionary containing volume profiles per symbol
        """
        volume_profiles = {}

        for symbol in self.symbols:
            # Get relevant data
            trades = trades_data[symbol]
            klines = klines_data[symbol]

            # Calculate buy/sell volume ratio from trades
            buy_volume = trades[trades["side"] == "BUY"]["quantity"].sum()
            sell_volume = trades[trades["side"] == "SELL"]["quantity"].sum()
            buy_sell_ratio = buy_volume / sell_volume if sell_volume > 0 else 1.0

            # Calculate volume momentum from klines
            volume_sma = (
                klines["volume"].rolling(window=self.lookback_periods["volume"]).mean()
            )
            volume_momentum = klines["volume"] / volume_sma

            volume_profiles[symbol] = pd.DataFrame(
                {
                    "buy_sell_ratio": buy_sell_ratio,
                    "volume_momentum": volume_momentum,
                    "volume_sma": volume_sma,
                }
            )

        return volume_profiles

    def calculate_volatility_metrics(
        self, klines_data: Dict[str, pd.DataFrame]
    ) -> Dict[str, pd.DataFrame]:
        """
        Calculate volatility metrics using OHLCV data.
        """
        vol_metrics = {}

        for symbol in self.symbols:
            klines = klines_data[symbol]

            # Calculate returns
            log_returns = np.log(klines["close"] / klines["close"].shift(1))

            # Calculate historical volatility
            hist_vol = log_returns.rolling(window=self.vol_window).std() * np.sqrt(
                24
            )  # Annualized

            # Calculate Parkinson volatility using high-low prices
            parkinsons_vol = np.sqrt(
                (np.log(klines["high"] / klines["low"]) ** 2) / (4 * np.log(2))
            ).rolling(window=self.vol_window).mean() * np.sqrt(24)

            # Garman-Klass volatility
            gk_vol = np.sqrt(
                0.5 * np.log(klines["high"] / klines["low"]) ** 2
                - (2 * np.log(2) - 1) * np.log(klines["close"] / klines["open"]) ** 2
            ).rolling(window=self.vol_window).mean() * np.sqrt(24)

            vol_metrics[symbol] = pd.DataFrame(
                {
                    "hist_vol": hist_vol,
                    "parkinsons_vol": parkinsons_vol,
                    "gk_vol": gk_vol,
                    "composite_vol": (hist_vol + parkinsons_vol + gk_vol) / 3,
                }
            )

        return vol_metrics

    def calculate_correlation_matrix(
        self, klines_data: Dict[str, pd.DataFrame]
    ) -> pd.DataFrame:
        """
        Calculate correlation matrix between assets.
        """
        returns_dict = {}

        for symbol in self.symbols:
            klines = klines_data[symbol]
            returns = np.log(klines["close"] / klines["close"].shift(1))
            returns_dict[symbol] = returns

        returns_df = pd.DataFrame(returns_dict)
        correlation_matrix = returns_df.rolling(
            window=self.lookback_periods["correlation"]
        ).corr()

        return correlation_matrix

    def calculate_momentum_signals(
        self, klines_data: Dict[str, pd.DataFrame]
    ) -> Dict[str, pd.DataFrame]:
        """
        Calculate momentum signals using multiple indicators.
        """
        momentum_signals = {}

        for symbol in self.symbols:
            klines = klines_data[symbol]

            # Calculate RSI
            delta = klines["close"].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            # Calculate MACD
            exp1 = klines["close"].ewm(span=12, adjust=False).mean()
            exp2 = klines["close"].ewm(span=26, adjust=False).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=9, adjust=False).mean()
            macd_hist = macd - signal

            # Calculate momentum score
            momentum_score = (
                0.4 * (rsi / 100)  # RSI component
                + 0.3 * (macd_hist / klines["close"])  # MACD component
                + 0.3
                * (
                    klines["close"].pct_change(self.lookback_periods["momentum"])
                )  # Price momentum
            )

            momentum_signals[symbol] = pd.DataFrame(
                {
                    "rsi": rsi,
                    "macd": macd,
                    "macd_hist": macd_hist,
                    "momentum_score": momentum_score,
                }
            )

        return momentum_signals

    def calculate_position_sizes(
        self,
        vol_metrics: Dict[str, pd.DataFrame],
        correlation_matrix: pd.DataFrame,
        volume_profiles: Dict[str, pd.DataFrame],
    ) -> Dict[str, float]:
        """
        Calculate position sizes based on volatility, correlation, and volume metrics.
        """
        position_sizes = {}

        # Calculate portfolio-level metrics
        total_risk_budget = 1.0  # Total risk to allocate
        vol_adjusted_limits = {}

        for symbol in self.symbols:
            # Get latest metrics
            vol = vol_metrics[symbol]["composite_vol"].iloc[-1]
            volume_momentum = volume_profiles[symbol]["volume_momentum"].iloc[-1]

            # Adjust position limit based on volatility
            vol_adjustment = np.exp(-vol / self.vol_threshold)
            vol_adjusted_limits[symbol] = self.position_limits[symbol] * vol_adjustment

            # Apply correlation penalty
            corr_penalty = correlation_matrix[symbol].abs().mean()
            if corr_penalty > self.max_correlation:
                vol_adjusted_limits[symbol] *= 1 - (corr_penalty - self.max_correlation)

            # Scale by volume momentum
            vol_adjusted_limits[symbol] *= np.clip(volume_momentum, 0.5, 2.0)

        # Normalize position sizes
        total_limit = sum(vol_adjusted_limits.values())
        for symbol in self.symbols:
            position_sizes[symbol] = (
                vol_adjusted_limits[symbol]
                / total_limit
                * total_risk_budget
                * self.leverage
            )

        return position_sizes

    def generate_signals(
        self, klines_data: Dict[str, pd.DataFrame], trades_data: Dict[str, pd.DataFrame]
    ) -> List[Order]:
        """
        Generate trading signals based on all available data.
        """
        # Calculate all required metrics
        volume_profiles = self.calculate_volume_profile(trades_data, klines_data)
        vol_metrics = self.calculate_volatility_metrics(klines_data)
        correlation_matrix = self.calculate_correlation_matrix(klines_data)
        momentum_signals = self.calculate_momentum_signals(klines_data)

        # Calculate position sizes
        position_sizes = self.calculate_position_sizes(
            vol_metrics, correlation_matrix, volume_profiles
        )

        # Generate orders
        orders = []

        for symbol in self.symbols:
            momentum = momentum_signals[symbol]["momentum_score"].iloc[-1]
            rsi = momentum_signals[symbol]["rsi"].iloc[-1]
            volume_profile = volume_profiles[symbol]

            # Current position
            current_position = self.positions.get(symbol)
            target_size = position_sizes[symbol]

            # Generate order based on signals
            if current_position is None:
                # Entry signals
                if (
                    rsi < self.rsi_thresholds[0]
                    and momentum < -0.2
                    and volume_profile["buy_sell_ratio"].iloc[-1] > 1.1
                ):
                    orders.append(
                        Order(
                            symbol=symbol,
                            side="BUY",
                            size=target_size,
                            order_type="MARKET",
                        )
                    )
                elif (
                    rsi > self.rsi_thresholds[1]
                    and momentum > 0.2
                    and volume_profile["buy_sell_ratio"].iloc[-1] < 0.9
                ):
                    orders.append(
                        Order(
                            symbol=symbol,
                            side="SELL",
                            size=target_size,
                            order_type="MARKET",
                        )
                    )
            else:
                # Exit signals
                if current_position.size > 0 and (
                    rsi > 60
                    or momentum < -0.1
                    or volume_profile["buy_sell_ratio"].iloc[-1] < 0.95
                ):
                    orders.append(
                        Order(
                            symbol=symbol,
                            side="SELL",
                            size=current_position.size,
                            order_type="MARKET",
                        )
                    )
                elif current_position.size < 0 and (
                    rsi < 40
                    or momentum > 0.1
                    or volume_profile["buy_sell_ratio"].iloc[-1] > 1.05
                ):
                    orders.append(
                        Order(
                            symbol=symbol,
                            side="BUY",
                            size=abs(current_position.size),
                            order_type="MARKET",
                        )
                    )

        return orders

    def update_positions(self, fills: List[Dict]):
        """
        Update positions based on order fills.
        """
        for fill in fills:
            symbol = fill["symbol"]
            size = fill["size"] * (1 if fill["side"] == "BUY" else -1)
            price = fill["price"]

            if symbol in self.positions:
                # Update existing position
                current_pos = self.positions[symbol]
                new_size = current_pos.size + size

                if new_size == 0:
                    # Position closed
                    self.historical_positions.append(current_pos)
                    del self.positions[symbol]
                else:
                    # Position modified
                    self.positions[symbol] = Position(
                        symbol=symbol,
                        size=new_size,
                        entry_price=price,
                        entry_time=datetime.now(),
                        trade_id=fill["trade_id"],
                    )
            else:
                # New position
                self.positions[symbol] = Position(
                    symbol=symbol,
                    size=size,
                    entry_price=price,
                    entry_time=datetime.now(),
                    trade_id=fill["trade_id"],
                )

    def calculate_risk_metrics(
        self, klines_data: Dict[str, pd.DataFrame]
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate risk metrics for current positions.
        """
        risk_metrics = {}

        for symbol, position in self.positions.items():
            klines = klines_data[symbol]
            current_price = klines["close"].iloc[-1]

            # Calculate unrealized PnL
            unrealized_pnl = (current_price - position.entry_price) * position.size
            unrealized_pnl_pct = (current_price / position.entry_price - 1) * 100

            # Calculate drawdown
            price_high = klines["high"][klines.index >= position.entry_time].max()
            drawdown = (current_price - price_high) / price_high * 100

            # Calculate volatility-adjusted stop loss
            vol = klines["close"].pct_change().std() * np.sqrt(24)
            dynamic_stop = position.entry_price * (1 - vol * 2)  # 2 std deviations

            risk_metrics[symbol] = {
                "unrealized_pnl": unrealized_pnl,
                "unrealized_pnl_pct": unrealized_pnl_pct,
                "drawdown": drawdown,
                "dynamic_stop": dynamic_stop,
                "current_price": current_price,
            }

        return risk_metrics

    def execute_risk_management(
        self,
        klines_data: Dict[str, pd.DataFrame],
        market_impact_threshold: float = 0.02,
    ) -> List[Order]:
        """
        Execute risk management rules and generate risk-based orders.
        """
        risk_orders = []
        risk_metrics = self.calculate_risk_metrics(klines_data)

        for symbol, metrics in risk_metrics.items():
            position = self.positions.get(symbol)
            if not position:
                continue

            # Check stop loss
            if metrics["current_price"] < metrics["dynamic_stop"] and position.size > 0:
                risk_orders.append(
                    Order(
                        symbol=symbol,
                        side="SELL",
                        size=position.size,
                        order_type="MARKET",
                    )
                )
            elif (
                metrics["current_price"] > metrics["dynamic_stop"] and position.size < 0
            ):
                risk_orders.append(
                    Order(
                        symbol=symbol,
                        side="BUY",
                        size=abs(position.size),
                        order_type="MARKET",
                    )
                )

            # Check drawdown limits
            if metrics["drawdown"] < -15:  # 15% drawdown limit
                risk_orders.append(
                    Order(
                        symbol=symbol,
                        side="SELL" if position.size > 0 else "BUY",
                        size=abs(position.size),
                        order_type="MARKET",
                    )
                )

            # Check position age
            position_age = (datetime.now() - position.entry_time).days
            if position_age > 5:  # 5-day maximum holding period
                risk_orders.append(
                    Order(
                        symbol=symbol,
                        side="SELL" if position.size > 0 else "BUY",
                        size=abs(position.size),
                        order_type="MARKET",
                    )
                )

        return risk_orders

    def calculate_market_impact(
        self,
        order: Order,
        trades_data: Dict[str, pd.DataFrame],
        klines_data: Dict[str, pd.DataFrame],
    ) -> float:
        """
        Estimate market impact for an order.
        """
        symbol = order.symbol
        trades = trades_data[symbol]
        klines = klines_data[symbol]

        # Calculate average trade size
        avg_trade_size = trades["quantity"].mean()

        # Calculate recent volume
        recent_volume = klines["volume"].iloc[-24:].sum()  # 24-hour volume

        # Estimate market impact
        size_impact = order.size / avg_trade_size
        volume_impact = order.size / recent_volume

        # Combine impacts
        market_impact = (0.7 * size_impact + 0.3 * volume_impact) * 0.01
        return market_impact

    def optimize_order_execution(
        self,
        orders: List[Order],
        trades_data: Dict[str, pd.DataFrame],
        klines_data: Dict[str, pd.DataFrame],
        max_market_impact: float = 0.02,
    ) -> List[Order]:
        """
        Optimize order execution to minimize market impact.
        """
        optimized_orders = []

        for order in orders:
            market_impact = self.calculate_market_impact(
                order, trades_data, klines_data
            )

            if market_impact > max_market_impact:
                # Split order into smaller chunks
                num_chunks = int(market_impact / max_market_impact) + 1
                chunk_size = order.size / num_chunks

                for i in range(num_chunks):
                    optimized_orders.append(
                        Order(
                            symbol=order.symbol,
                            side=order.side,
                            size=chunk_size,
                            order_type="LIMIT",
                            price=self._calculate_limit_price(
                                order, klines_data[order.symbol], i, num_chunks
                            ),
                        )
                    )
            else:
                optimized_orders.append(order)

        return optimized_orders

    def _calculate_limit_price(
        self, order: Order, klines: pd.DataFrame, chunk_index: int, total_chunks: int
    ) -> float:
        """
        Calculate optimal limit price for order chunk.
        """
        current_price = klines["close"].iloc[-1]
        avg_spread = (klines["high"] - klines["low"]).mean()

        # Calculate price adjustment based on chunk position
        adjustment = (chunk_index / total_chunks) * avg_spread

        if order.side == "BUY":
            return current_price * (1 + adjustment)
        else:
            return current_price * (1 - adjustment)

    def run_iteration(
        self, klines_data: Dict[str, pd.DataFrame], trades_data: Dict[str, pd.DataFrame]
    ) -> List[Order]:
        """
        Run a complete iteration of the quant.
        klines_data : Dict[str, pd.DataFrame] = {"symbol_1": klines_df_2, "symbol_2": klines_df_2}
        trades_data : Dict[str, pd.DataFrame] = {"symbol_1": trades_df_2, "symbol_2": trades_df_2}
        """
        # Generate primary trading signals
        signal_orders = self.generate_signals(klines_data, trades_data)

        # Generate risk management orders
        risk_orders = self.execute_risk_management(klines_data)

        # Combine all orders
        all_orders = signal_orders + risk_orders

        # Optimize order execution
        optimized_orders = self.optimize_order_execution(
            all_orders, trades_data, klines_data
        )

        return optimized_orders
