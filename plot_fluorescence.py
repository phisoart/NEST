import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

def convert_time_to_hours(time_str):
    """Convert 'h:mm' time string to decimal hours."""
    try:
        hours, minutes = map(int, time_str.split(':'))
        return hours + minutes / 60.0
    except:
        return np.nan

def plot_fluorescence_data(csv_file='fluorescence_analysis.csv', output_basename='fluorescence_plot'):
    """Generate a publication-style plot from the CSV data."""
    if not os.path.exists(csv_file):
        print(f"Error: {csv_file} not found.")
        return

    # 1. Load and preprocess data
    df = pd.read_csv(csv_file)
    df['time_hours'] = df['time_str'].apply(convert_time_to_hours)

    # Calculate hourly mean for Ctr data
    ctr_mean = df[df['sample_type'] == 'Ctr'].groupby('time_hours')['mean_intensity'].mean().reset_index()
    ctr_mean.rename(columns={'mean_intensity': 'Ctr_mean'}, inplace=True)

    # Filter SA data only
    sa_df = df[df['sample_type'] == 'SA'].copy()
    
    # Merge Ctr mean into SA data
    merged_df = pd.merge(sa_df, ctr_mean, on='time_hours', how='left')

    # Calculate Δ Intensity
    merged_df['delta_intensity'] = merged_df['mean_intensity'] - merged_df['Ctr_mean']

    # 2. Aggregate data for plotting
    plot_data = merged_df.groupby(['time_hours', 'cfu'])['delta_intensity'].agg(['mean', 'std']).reset_index()

    # 3. Plotting
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(10, 8))

    # Color palette similar to the paper
    colors = {
        1: '#4B8B9E',    # Blue-green
        5: '#5FAD98',    # Green
        10: '#D6A46A',   # Orange
        50: '#C75D4B',   # Red
        100: '#A52A2A'   # Brown-red
    }
    
    cfu_levels = sorted(plot_data['cfu'].unique())

    for cfu in cfu_levels:
        group = plot_data[plot_data['cfu'] == cfu]
        color = colors.get(cfu, 'gray')
        
        ax.plot(group['time_hours'], group['mean'],
                marker='o',
                linestyle='-',
                color=color,
                label=f'{cfu} CFU')
        
        ax.fill_between(group['time_hours'],
                        group['mean'] - group['std'],
                        group['mean'] + group['std'],
                        color=color,
                        alpha=0.2)

    # Add Threshold line
    threshold_value = 4000
    ax.axhline(y=threshold_value, color='black', linestyle='--', linewidth=1.5, zorder=1)
    ax.text(-0.4, threshold_value + 1000, 'Threshold', verticalalignment='center', fontsize=14, fontweight='bold')
    
    # 4. Styling and labels
    ax.set_title('S. aureus', fontsize=18, fontweight='bold', pad=20)
    ax.set_xlabel('Incubation time [hour]', fontsize=16, labelpad=15)
    ax.set_ylabel('Δ Intensity [a.u.]', fontsize=16, labelpad=15)
    
    ax.tick_params(axis='both', which='major', labelsize=14)
    
    ax.set_xlim(-0.5, 12.5)
    ax.set_ylim(-5000, 30000)
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    legend = ax.legend(title='CFU', fontsize=12)
    plt.setp(legend.get_title(), fontsize=14)

    # 5. Save plot (multiple formats)
    plt.tight_layout()

    output_formats = {
        'png': {'dpi': 300},
        'svg': {},
        'pdf': {}
    }
    
    saved_files = []
    for fmt, options in output_formats.items():
        filename = f"{output_basename}.{fmt}"
        plt.savefig(filename, **options)
        saved_files.append(filename)
    
    print(f"Plot saved to the following files: {', '.join(saved_files)}")
    plt.show()

if __name__ == '__main__':
    plot_fluorescence_data() 