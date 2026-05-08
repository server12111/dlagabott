import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from io import BytesIO


def _base_style():
    plt.rcParams.update({
        "figure.facecolor": "#1e1e2e",
        "axes.facecolor": "#1e1e2e",
        "axes.edgecolor": "#4a4a6a",
        "axes.labelcolor": "#cdd6f4",
        "xtick.color": "#cdd6f4",
        "ytick.color": "#cdd6f4",
        "text.color": "#cdd6f4",
        "grid.color": "#313244",
        "grid.linestyle": "--",
        "grid.alpha": 0.6,
        "font.size": 11,
    })


def create_bar_chart(labels: list, values: list, title: str, color: str = "#89b4fa") -> BytesIO:
    _base_style()

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(labels, values, color=color, width=0.6, zorder=3)
    ax.set_title(title, pad=12, fontsize=13, fontweight="bold", color="#cba6f7")
    ax.set_ylabel("Количество", labelpad=8)
    ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    ax.grid(axis="y", zorder=0)
    ax.set_axisbelow(True)

    for bar in bars:
        height = bar.get_height()
        if height > 0:
            ax.annotate(
                str(int(height)),
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 4),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=10,
                color="#a6e3a1",
            )

    if len(labels) > 8:
        plt.xticks(rotation=45, ha="right")

    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format="png", dpi=130, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf
