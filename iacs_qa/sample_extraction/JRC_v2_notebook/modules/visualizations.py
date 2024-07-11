import ipywidgets as widgets
import matplotlib.pyplot as plt
from IPython.display import display, clear_output, HTML
import io


def calculate_holding_with_most_interventions_selected(datamanager):
    # calculate the holding with the most interventions selected
    holding_interventions = {}
    for bucket in datamanager.final_bucket_state.values():
        for parcel in bucket["parcels"]:
            holding = parcel["gsa_hol_id"]
            if holding in holding_interventions:
                holding_interventions[holding] += 1
            else:
                holding_interventions[holding] = 1
    holding_with_most_interventions = max(holding_interventions, key=holding_interventions.get)
    return holding_with_most_interventions, holding_interventions[holding_with_most_interventions]


def all_parcels_in_buckets(buckets):
    """
    Count all parcels in buckets. Identify parcels by their par_id and hol_id.
    """
    all_parcels = []
    for bucket in buckets.values():
        for parcel in bucket["parcels"]:
            unique_parcel_id = str(parcel["gsa_par_id"]) + "_" + str(parcel["gsa_hol_id"])
            all_parcels.append(unique_parcel_id)
    return set(all_parcels)

def count_unique_selected_parcels_per_holding(all_selected_parcels):
    parcels_per_holding = {}
    for a in all_selected_parcels:
        par_id = a.split("_")[0]
        hol_id = a.split("_")[1]
        if hol_id in parcels_per_holding:
            parcels_per_holding[hol_id].add(par_id)
        else:
            parcels_per_holding[hol_id] = {par_id}

    # count the number of unique parcels per holding
    count_per_holding = {hol_id: len(parcels) for hol_id, parcels in parcels_per_holding.items()}

    # calculate the average number of parcels per holding
    avg_parcels_per_holding = sum(count_per_holding.values()) / len(count_per_holding)
    return count_per_holding, avg_parcels_per_holding

def count_selected_covered_parcels(datamanager):
    covered_parcels = []
    noncovered_parcels = []
    for bucket in datamanager.final_bucket_state.values():
        for parcel in bucket["parcels"]:
            if parcel["covered"] == 1:
                unique_parcel_id = str(parcel["gsa_par_id"]) + "_" + str(parcel["gsa_hol_id"])
                covered_parcels.append(unique_parcel_id)
            else:
                noncovered_parcels.append(unique_parcel_id)

    return len(set(covered_parcels)), len(set(noncovered_parcels))

def display_statistics_summary(datamanager):
    total_rows = len(datamanager.parcels_df)
    selected_rows = sum([len(bucket['parcels']) for bucket in datamanager.final_bucket_state.values()])

    # a unique parcel has a unique par_id and hol_id
    # I assume that there can be multiple parcels with the same gsa_par_id but different gsa_hol_id
    all_unique_parcels_count = len(datamanager.parcels_df.drop_duplicates(subset=["gsa_par_id", "gsa_hol_id"]))
    all_selected_parcels = all_parcels_in_buckets(datamanager.final_bucket_state)
    all_selected_parcels_count = len(all_selected_parcels)

    avg_par_per_hol = count_unique_selected_parcels_per_holding(all_selected_parcels)[1]
    
    total_holdings = len(datamanager.parcels_df["gsa_hol_id"].unique())
    selected_holdings = len(datamanager.added_holdings)
    avg_int_per_holding = selected_rows / selected_holdings
    most_interventions = calculate_holding_with_most_interventions_selected(datamanager)

    all_buckets_full = all([bucket["target"] == len(bucket["parcels"]) for bucket in datamanager.final_bucket_state.values()])
    if all_buckets_full:
        bucket_status_label = widgets.Label(value="All buckets are full!")
        bucket_status_label.add_class("green_label_bold")
    else:
        bucket_status_label = widgets.Label(value="Not all buckets are full. See progress indicators for details.")
        bucket_status_label.add_class("orange_label_bold")

    title_label = widgets.Label(value="Summary statistics:")
    title_label.add_class("title_label")

    sp_label = widgets.Label(value=f"Selected individual parcels: {all_selected_parcels_count} / {all_unique_parcels_count} ({all_selected_parcels_count/all_unique_parcels_count*100:.2f}%)")
    sp_label.add_class("black_label_bold")
    tsr_label = widgets.Label(value=f"(Total selected rows: {selected_rows} / {total_rows} ({selected_rows/total_rows*100:.2f}%))")

    sh_label = widgets.Label(value=f"Selected holdings: {selected_holdings} / {total_holdings} ({selected_holdings/total_holdings*100:.2f}%)")
    sh_label.add_class("black_label_bold")

    asppsh_label = widgets.Label(value=f"Average number of selected parcels per selected holding: {avg_par_per_hol:.2f}")
    asppsh_label.add_class("black_label_bold")

    asrpsh_label = widgets.Label(value=f"(Average selected rows per selected holding: {avg_int_per_holding:.2f})")

    count_per_holding, _ = count_unique_selected_parcels_per_holding(all_selected_parcels)
    holding_with_highest_count = max(count_per_holding, key=count_per_holding.get)
    hwmrs_label = widgets.Label(value=f"Holding with most parcels selected: '{holding_with_highest_count}' ({count_per_holding[holding_with_highest_count]} parcels)")

    vbox = widgets.VBox([title_label, 
                         bucket_status_label, 
                         sp_label, 
                         sh_label, 
                         asppsh_label, 
                         #hwmrs_label,
                         ], 
                         layout=widgets.Layout(padding="10px"))

    display(vbox)

def calculate_stats_for_reused_parcels(datamanager):
    counts_for_parcels = {}

    for bucket_id, bucket in datamanager.final_bucket_state.items():
        for parcel in bucket["parcels"]:
            parcel_id = str(parcel["gsa_par_id"]) + "_" + str(parcel["gsa_hol_id"])
            if parcel_id in counts_for_parcels:
                counts_for_parcels[parcel_id] += 1
            else:
                counts_for_parcels[parcel_id] = 1

    histogram_buckets = {}
    for parcel_id, count in counts_for_parcels.items():
        if count in histogram_buckets:
            histogram_buckets[count] += 1
        else:
            histogram_buckets[count] = 1
    
    return histogram_buckets


def reused_histogram_widget(datamanager):
    histogram_buckets = calculate_stats_for_reused_parcels(datamanager)

    sorted_buckets = dict(sorted(histogram_buckets.items()))

    # Get keys and values
    keys = list(sorted_buckets.keys())
    values = list(sorted_buckets.values())

    # Generate a colormap
    # colors = plt.cm.viridis(np.linspace(0, 1, len(keys)))

    # Set the figure size to make the chart flatter and more compact
    figsize = (5, 3)
    plt.figure(figsize=figsize)  # Width 8, Height 4

    # Create the bar plot
    plt.bar(keys, values, color="#1daee3")

    # Add labels to each bar with smaller font size
    for i, value in enumerate(values):
        plt.text(keys[i], value + 5, str(value), ha="center", fontsize=8)

    # Create x-axis labels
    xaxis_labels = [f"Parcels found in {k} buckets" if k > 1 else "Parcels found in 1 bucket" for k in keys]

    # Set title and labels with smaller font sizes
    plt.title("Parcels found in multiple ua_group buckets", fontsize=10)
    plt.xlabel("")
    plt.ylabel("Number of parcels", fontsize=10)
    plt.xticks(keys, xaxis_labels, rotation=45, ha="right", fontsize=8)  # Use custom labels and rotate them
    plt.yticks(fontsize=8)  # Smaller font size for y-axis ticks

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close()

    return widgets.Image(value=buf.getvalue(), format='png')#, width=figsize[0]*25, height=figsize[1]*25)

def display_covered_parcels_piechart(datamanager):
    covered, noncovered = count_selected_covered_parcels(datamanager)
    # Function to create a pie chart and return it as an image widget
    def create_pie_chart(covered, noncovered, figsize=(7, 7)):
        fig, ax = plt.subplots(figsize=figsize)  # Adjust size here
        sizes = [covered, noncovered]
        labels = ['Covered', 'Non-covered']
        colors = ['#1daee3', '#DFDFDF']
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140, textprops={'fontsize': 14})
        
        # Set the font size of the labels dynamically
        for text in texts:
            text.set_fontsize(40) 
        for autotext in autotexts:
            autotext.set_fontsize(40)
        
        ax.axis('equal')
        plt.title("Selected parcels covered by VHR images", fontsize=40)
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)
        return widgets.Image(value=buf.getvalue(), format='png', width=figsize[0]*25, height=figsize[1]*25)

    pcs = 12

    covered_pie_widget = create_pie_chart(covered, noncovered, figsize=(pcs, pcs))

    #display(covered_pie_widget)
    return covered_pie_widget

def display_reused_and_covered(datamanager):
    histogram = reused_histogram_widget(datamanager)
    piechart = display_covered_parcels_piechart(datamanager)
    grid = widgets.GridBox([histogram, piechart], layout=widgets.Layout(grid_template_columns="repeat(2, 500px)", padding="1px"))
    display(grid)

def display_bucket_pie_charts(datamanager):
    # total statistic (top)
    total_rows = len(datamanager.parcels_df)
    selected_rows = sum([len(bucket['parcels']) for bucket in datamanager.final_bucket_state.values()])
    total_holdings = len(datamanager.parcels_df["gsa_hol_id"].unique())
    selected_holdings = len(datamanager.added_holdings)

    # Function to create a pie chart and return it as an image widget
    def create_pie_chart(selected, total, title, figsize=(7, 7)):
        fig, ax = plt.subplots(figsize=figsize)  # Adjust size here
        sizes = [selected, total - selected]
        labels = ['Selected', 'Remaining']
        colors = ['#31C800', '#DFDFDF']
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140, textprops={'fontsize': 14})
        
        # Set the font size of the labels dynamically
        for text in texts:
            text.set_fontsize(40) 
        for autotext in autotexts:
            autotext.set_fontsize(40)
        
        ax.axis('equal')
        plt.title(title, fontsize=40)
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)
        return widgets.Image(value=buf.getvalue(), format='png', width=figsize[0]*25, height=figsize[1]*25)

    pcs = 15

    rows_pie_widget = create_pie_chart(selected_rows, total_rows, f"Selected interventions ({selected_rows} / {total_rows})", figsize=(pcs, pcs))
    holdings_pie_widget = create_pie_chart(selected_holdings, total_holdings, f"Selected holdings ({selected_holdings} / {total_holdings})", figsize=(pcs, pcs))

    # create a horizontal box to display the pie charts side by side
    hbox = widgets.HBox([rows_pie_widget, holdings_pie_widget], layout=widgets.Layout(justify_content='space-around'))

    bucket_stats_widget_list = []
    for bucket_id, info in datamanager.ua_groups.items():
        label = info["desc"]
        selected = info["selected"]
        total = info["count"]
        title_label = widgets.Label(value=label)
        if selected == info["target"]:
            title_label.add_class("green_label_bold")
            title_label.value += " (target reached)"
        else:
            title_label.add_class("orange_label_bold")
            title_label.value += f" (target not reached)"
        selected_label = widgets.Label(value=f"Selected: {selected} / {total} ({selected/total*100:.2f}%) Target: {info['target']}")
        bucket_pie_widget = create_pie_chart(selected, total, bucket_id, figsize=(10,10))
        vbox = widgets.VBox([title_label, selected_label, bucket_pie_widget], layout=widgets.Layout(padding="10px"))
        bucket_stats_widget_list.append(vbox)

    buckets_grid = widgets.GridBox(bucket_stats_widget_list, layout=widgets.Layout(grid_template_columns="repeat(3, 350px)", padding="10px"))
    
    vbox = widgets.VBox([hbox, buckets_grid], layout=widgets.Layout(padding="10px"))

    # a lot of this function is not used now, refactor
    display(buckets_grid)


def display_bucket_stats(datamanager):
    def create_fraction_bar(selected, total, title, figsize=(5, 1)):
        fig, ax = plt.subplots(figsize=figsize)
        
        fraction = selected / total
        ax.barh(0, fraction, height=0.5, color='#1daee3')
        ax.barh(0, 1-fraction, left=fraction, height=0.5, color='#DFDFDF')
        ax.set_xlim(0, 1)
        ax.set_yticks([])
        ax.set_xticks([])
        
        # Add labels
        ax.text(0.5, 0, f'{selected}/{total} ({fraction:.1%})', 
                ha='center', va='center', fontweight='bold', fontsize=18)
        
        #plt.title(title, fontsize=18, pad=20)
        
        plt.tight_layout()
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
        buf.seek(0)
        plt.close(fig)
        return widgets.Image(value=buf.getvalue(), format='png', width=figsize[0]*50, height=figsize[1]*50)

    bucket_stats_widget_list = []
    for bucket_id, info in datamanager.ua_groups.items():
        label = info["desc"]
        selected = info["selected"]
        total = info["count"]
        title_label = widgets.Label(value=label, style={'font_size': '14px', 'font_weight': 'bold'})
        if selected == info["target"]:
            title_label.add_class("green_label_bold")
            title_label.value += " (target reached)"
        else:
            title_label.add_class("orange_label_bold")
            title_label.value += f" (target not reached)"
        selected_label = widgets.Label(value=f"Selected: {selected} / {total} ({selected/total*100:.2f}%) Target: {info['target']}", 
                                       style={'font_size': '14px'})
        bucket_widget = create_fraction_bar(selected, total, bucket_id)
        vbox = widgets.VBox([title_label, selected_label, bucket_widget], 
                            layout=widgets.Layout(padding="10px", align_items='center', width='300px'))
        bucket_stats_widget_list.append(vbox)

    buckets_grid = widgets.GridBox(bucket_stats_widget_list, 
                                   layout=widgets.Layout(grid_template_columns="repeat(3, 320px)", 
                                                         grid_gap='15px', 
                                                         padding="10px"))
    
    display(buckets_grid)