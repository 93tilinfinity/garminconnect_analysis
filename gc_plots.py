import matplotlib.pyplot as plt
import pandas as pd

def uni_plot(df):
    fig, ax1 = plt.subplots()
    color = 'tab:red'
    ax1.set_xlabel('Timestamp')
    ax1.set_ylabel('Heart Rate (bpm)', color=color)
    ax1.plot(df['HeartRate'].index, df['HeartRate'], color=color)
    ax1.tick_params(axis='y', labelcolor=color)

    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
    color2 = 'tab:blue'
    ax2.set_ylabel('AirTemperature (C)', color=color2)  # we already handled the x-label with ax1
    ax2.plot(df['HeartRate'].index, df['AirTemperature'], color=color2)
    ax2.tick_params(axis='y', labelcolor=color2)
    fig.tight_layout()  # otherwise the right y-label is slightly clipped
    plt.show()

def plot_box(data):
    colors = ['pink', 'lightblue', 'lightgreen']
    col_idx = 0
    if len(data) > 1:
        fig, axes = plt.subplots(nrows=len(data), ncols=1, sharex=True, figsize=(15, 9))
        for ax, d in zip(axes, data):
            bplot = ax.boxplot([r['full']['HeartRate'] for r in d],
                               vert=True,
                               patch_artist=True)
            for patch in bplot['boxes']:
                patch.set_facecolor(colors[col_idx])
            col_idx += 1
            ax.yaxis.grid(True)
            ax.set_ylabel('Heart Rate (bpm)')
    else:
        fig, axes = plt.subplots(nrows=len(data), ncols=1, sharex=True, figsize=(10, 6))
        bplot = axes.boxplot([r['full']['HeartRate'] for r in data[0]],
                             vert=True,
                             patch_artist=True)

        for patch in bplot['boxes']:
            patch.set_facecolor(colors[col_idx])

        axes.yaxis.grid(True)
        axes.set_ylabel('Heart Rate (bpm)')

    plt.xlabel('Garmin Session')
    plt.show()

def expose_outliers(res1,res2):
    count = 0
    fig, ax1 = plt.subplots()
    ax1.set_xlabel('Session')
    ax1.set_ylabel('Heart Rate (bpm)')
    for r1,r2 in zip(res1,res2):
        ax1.scatter(len(r2['full'])*[count],r2['full']['HeartRate'],color='tab:red',s=9)
        ax1.scatter(len(r1['full'])*[count],r1['full']['HeartRate'],color='tab:blue',s=9)
        count += 1
    fig.tight_layout()
    plt.show()
    print(count)

# 16 - scatter plots of summary stats!
def plot_scatter(df,cols=['HRmax','HRavg','Duration','HRstd','TempAvg']):
    colors = ['hotpink', 'grey', 'royalblue']
    fig, axes = plt.subplots(nrows=len(cols), ncols=1, sharex=True, figsize=(5,10))
    for ax, col in zip(axes, cols):
        for typ in set(df['ActivityCode']):
            temp = df[df['ActivityCode'] == typ]
            if col == 'Duration':
                y = [t.seconds/60 for t in temp[col]]
            else:
                y = temp[col]
            ax.scatter(temp.index, y, marker='x',color = colors[typ % len(colors)])
            ax.grid()
            ax.set_ylabel(col)
    plt.xlabel('Garmin Session Date')
    plt.xticks(rotation=45)
    plt.legend(['Indoor Cycling', 'Indoor Rowing', 'Outdoor Cycling'])
    fig.tight_layout()
    plt.show()

# 17
def plot_scatter_type(df):
    colors = ['hotpink', 'grey', 'royalblue']
    fig, ax = plt.subplots(nrows=1, ncols=1, sharex=True, figsize=(6,4))
    for typ in set(df['ActivityCode']):
        temp = df[df['ActivityCode'] == typ]
        x = [t.seconds / 60 for t in temp['Duration']]
        y = temp['HRavg'].values
        ax.scatter(x, y, marker='o',color = colors[typ % len(colors)])
    ax.grid()
    plt.ylabel('Average HR (bpm)')
    plt.xlabel('Session Duration (mins)')
    plt.xticks(rotation=45)
    plt.legend(['Indoor Cycling','Indoor Rowing','Outdoor Cycling'])
    fig.tight_layout()
    plt.show()

def time_bars(data):
    colors = ['hotpink','grey','royalblue']
    zn = pd.DataFrame([d['zone'] for d in data],\
                      [d['full'].index[0] for d in data])
    zn['activitycode'] = [d['meta']['activitycode'] for d in data]
    zn = zn.sort_index()

    zn_0 = zn[zn['activitycode'] == 0].drop(columns='activitycode')
    zn_1 = zn[zn['activitycode'] == 1].drop(columns='activitycode')
    zn_2 = zn[zn['activitycode'] == 2].drop(columns='activitycode')

    zn_sum = pd.DataFrame({i:[zn_0[i].sum(),zn_1[i].sum(),zn_2[i].sum()] for i in zn_0.columns})
    zn_sum.index = ['Indoor Cycling','Indoor Rowing','Outdoor Cycling']
    zn_sum = zn_sum.T

    ax = zn_sum.plot(kind='bar',color=colors)
    ax.set_ylabel('Time (mins)')
    ax.grid()
    plt.xticks(rotation=45)
    plt.title('Time Spent in HR Zone')
    plt.tight_layout()
    plt.show()