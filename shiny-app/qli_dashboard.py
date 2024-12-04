from shiny import App, render, ui
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from geopy.distance import geodesic
import os

base_directory = '/Users/francescaleon/Documents/GitHub/DAPII/dap2_final_project/data/'
topic_averages = pd.read_excel(os.path.join(base_directory, "topic_averages.xlsx"))

# Coordinates for capitals
capital_coords = {
    "Argentina": (-34.6037, -58.3816),
    "Bolivia": (-16.5000, -68.1500),
    "Brazil": (-15.8267, -47.9218),
    "Chile": (-33.4489, -70.6693),
    "Colombia": (4.7110, -74.0721),
    "Ecuador": (-0.1807, -78.4678),
    "Paraguay": (-25.2637, -57.5759),
    "Peru": (-12.0464, -77.0428),
    "Uruguay": (-34.9011, -56.1645),
    "Venezuela": (10.4806, -66.9036),
}

# Function to calculate flight times
def calculate_flight_times(home_country):
    home_coords = capital_coords[home_country]
    flight_times = {
        country: geodesic(home_coords, coords).km / 800
        for country, coords in capital_coords.items()
    }
    return flight_times

# Define UI
app_ui = ui.page_fluid(
    ui.tags.style("""
        h3, h4 {
            font-weight: bold; /* Make all h3 and h4 titles bold */
        }
        .slider-container {
            display: flex;
            align-items: center;
        }
        .slider-label {
            margin-right: 5px;
            font-weight: bold;
        }
        .tooltip-icon {
            color: black;
            cursor: help;
            margin-left: 5px;
        }
    """),
    ui.h1("Quality of Life Index (QLI) for Latin American Countries", style="text-align: center; margin-bottom: 30px; text-decoration: underline; font-weight: bold;"),
    ui.row(
        # Left Panel
        ui.column(
            4,
            ui.h3("Home Country"),
            ui.tags.p("Select home country", 
              style="font-size: 12px; color: gray; margin-top: -5px;"),
            ui.input_select("home_country", None, list(capital_coords.keys())),
            ui.h3("Rank the Topics"),
            ui.tags.p("1 is the highest rank, 5 is the lowest rank.", 
              style="font-size: 12px; color: gray; margin-top: -5px;"),
            ui.tags.div(
                ui.tags.span("Economic Factors", class_="slider-label"),
                ui.tags.span(
                    " ⓘ", 
                    class_="tooltip-icon", 
                    title="Includes: Unemployment Rate, GDP Per Capita, Inflation Rate, Poverty Rate, Population below poverty line."
                ),
                class_="slider-container"
            ),
            ui.input_slider("economic_factors", None, min=1, max=5, value=3),
            ui.tags.div(
                ui.tags.span("Health and Well-being", class_="slider-label"),
                ui.tags.span(
                    " ⓘ", 
                    class_="tooltip-icon", 
                    title="Includes: Life Expectancy, Hospital Beds per 1,000 People, Infant Mortality Rate, Access to Essential Services, Mean levels of fine particulate matter."
                ),
                class_="slider-container"
            ),
            ui.input_slider("health_wellbeing", None, min=1, max=5, value=3),
            ui.tags.div(
                ui.tags.span("Safety and Governance", class_="slider-label"),
                ui.tags.span(
                    " ⓘ", 
                    class_="tooltip-icon", 
                    title="Includes: Crime Rates, Confidence in the Police, Ratio of Average Income between Women and Men."
                ),
                class_="slider-container"
            ),
            ui.input_slider("safety_governance", None, min=1, max=5, value=3),
            ui.tags.div(
                ui.tags.span("Education", class_="slider-label"),
                ui.tags.span(
                    " ⓘ", 
                    class_="tooltip-icon", 
                    title="Includes: School Enrollment Rates, Public Expenditure on Education."
                ),
                class_="slider-container"
            ),
            ui.input_slider("education", None, min=1, max=5, value=3),
            ui.tags.div(
                ui.tags.span("Social and Environmental", class_="slider-label"),
                ui.tags.span(
                    " ⓘ", 
                    class_="tooltip-icon", 
                    title="Includes: Population Reporting Trust in Other People, Migration Rate, Gini Index, Population that has Considered Migrating, Life Satisfaction Index."
                ),
                class_="slider-container"
            ),
            ui.input_slider("social_environmental", None, min=1, max=5, value=3),
            ui.h3("Top Countries to Migrate"),
            ui.tags.p("Ranking calculated based on personalized QLI. Initial QLI gives equal weight to all topics. Personalized QLI calculated based on preferences weight.", 
              style="font-size: 12px; color: gray; margin-top: -5px;"),
            ui.output_table("ranking_table")
        ),
        # Right Panel
        ui.column(
            8,
            ui.h3("Personalized QLI and Flight Times between Capitals"),
            ui.tags.p("Personalized QLI used for coloring countries. Flight time calculated using the shortest distance between home country capital and other countries capitals, assuming a constant flight average speed of 800 km/h.", 
              style="font-size: 12px; color: gray; margin-top: -5px;"),
            ui.output_ui("flight_map"),
            ui.h3("Quality of Life Index by Topic"),
            ui.tags.p("Quality of Life Index (QLI) calculated by standardizing each indicator and taking the mean by topic.", 
              style="font-size: 12px; color: gray; margin-top: -5px;"),
            ui.output_ui("spider_chart")
        )
    )
)

# Server Logic
def server(input, output, session):
    def calculate_personalized_qli():
        rankings = {
            "Economic Factors": input.economic_factors(),
            "Health and Well-being": input.health_wellbeing(),
            "Safety and Governance": input.safety_governance(),
            "Education": input.education(),
            "Social and Environmental": input.social_environmental(),
        }

        weights = {topic: (6 - rank) ** 2 for topic, rank in rankings.items()}
        total_weight = sum(weights.values())
        weights = {topic: weight / total_weight for topic, weight in weights.items()}

        topic_columns = ["Economic Factors", "Health and Well-being", "Safety and Governance", "Education", "Social and Environmental"]
        topic_averages["Initial QLI"] = topic_averages[topic_columns].mean(axis=1)
        topic_averages["Personalized QLI"] = topic_averages[topic_columns].dot([weights[col] for col in topic_columns])

    @output
    @render.table
    def ranking_table():
        calculate_personalized_qli()
        ranked = topic_averages.sort_values("Personalized QLI", ascending=False).head(5)
        return ranked[["Country", "Initial QLI", "Personalized QLI"]].round(2)

    @output
    @render.ui
    def spider_chart():
        topic_columns = ["Economic Factors", "Health and Well-being", "Safety and Governance", "Education", "Social and Environmental"]
        categories = topic_columns + [topic_columns[0]]
        fig = go.Figure()

        for _, row in topic_averages.iterrows():
            values = list(row[topic_columns]) + [row[topic_columns[0]]]
            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=categories,
                fill='toself',
                name=row["Country"],
                opacity=0.6
            ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 1])
            ),
            showlegend=True,
            legend_title=dict(text="Select countries:"),
            template="plotly_white",
            colorway=px.colors.sequential.Cividis,
            paper_bgcolor="white"
        )

        return ui.HTML(fig.to_html(full_html=False))

    @output
    @render.ui
    def flight_map():
        calculate_personalized_qli()
        home_country = input.home_country()

        flight_times = calculate_flight_times(home_country)
        topic_averages["Flight Time (hrs)"] = topic_averages["Country"].map(flight_times)
        
        fig = px.choropleth(
            topic_averages,
            locations="Country",
            locationmode="country names",
            color="Personalized QLI",
            hover_name="Country",
            color_continuous_scale="cividis"
        )

        for _, row in topic_averages.iterrows():
            fig.add_trace(go.Scattergeo(
                lon=[capital_coords[row["Country"]][1]],
                lat=[capital_coords[row["Country"]][0]],
                text=f"{row['Country']}: {row['Flight Time (hrs)']:.1f} hrs",
                marker=dict(
                    size=row["Flight Time (hrs)"] * 5,
                    color="peru",
                    opacity=0.7
                ),
                showlegend=False
            ))

        fig.update_geos(fitbounds="locations", visible=True)
        fig.update_layout(
            height=500,
            template="plotly_white",
            coloraxis_colorbar_title="Personalized QLI"
        )

        return ui.HTML(fig.to_html(full_html=False))

# Create App
app = App(app_ui, server)

if __name__ == "__main__":
    app.run()



















         

















