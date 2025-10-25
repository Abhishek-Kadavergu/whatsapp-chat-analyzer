from datetime import datetime

import streamlit as st
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import preprocessor, helper
import plotly.express as px
import seaborn as sns
import numpy as np
from pymongo import MongoClient
from dotenv import load_dotenv
import os
load_dotenv()
mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri)
db = client["whatsapp_analyzer"]
collection = db["chats"]

st.title("WhatsApp Chat Analyzer")
st.markdown("Upload your exported whatsapp chat here and view the analysis")
st.sidebar.title("WhatsApp Chat Analyzer 📊")
uploaded_file = st.file_uploader("Upload your WhatsApp chat (.txt)", type=["txt"])
if uploaded_file is not None:
    bytes_data = uploaded_file.getvalue()
    data = bytes_data.decode('utf-8')
    # st.text(data)
    df = preprocessor.preprocess(data)
    st.dataframe(df)

    # Store in MongoDB
    chat_data = {
        "filename": uploaded_file.name,
        "content": data,
        "uploaded_at": datetime.utcnow(),
    }

    # Insert into MongoDB
    result = collection.insert_one(chat_data)
    # print(result)

    # st.success(f"✅ Chat saved to DB with ID: {result.inserted_id}")
    # st.write(f"Total chats in DB: {collection.count_documents({})}")


    # fetch unique users
    user_list = df["user"].unique().tolist()
    user_list.remove("group_notification")
    user_list.sort()
    user_list.insert(0, "Overall")
    selected_user = st.sidebar.selectbox("Show Analysis wrt: ", user_list)

    if st.sidebar.button("Show Analysis"):
        num_messages, words, num_media_messages, num_links = helper.fetch_stats(selected_user, df)
        st.title("Top Statistics ")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.header("Total Messages")
            st.title(num_messages)
        with col2:
            st.header("Total Words")
            st.title(words)
        with col3:
            st.header("Media Shared ")
            st.title(num_media_messages)
        with col4:
            st.header("Links Shared ")
            st.title(num_links)



        # activity map
        st.title("🗺️ Activity Map")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🌟 Most busy day")
            busy_day = helper.week_activity_map(selected_user, df)
            fig_day = px.bar(
                busy_day,
                x=busy_day.index,
                y=busy_day.values,
                color=busy_day.values,
                color_continuous_scale="plasma",
                text=busy_day.values,
                title="Most Active Days",
            )
            fig_day.update_traces(textposition="outside", marker_line_color="white", marker_line_width=1.5)
            fig_day.update_layout(
                plot_bgcolor="#0E1117",
                paper_bgcolor="#0E1117",
                font_color="white",
                title_font_size=18,
                title_x=0.5,
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=False),
            )
            st.plotly_chart(fig_day, use_container_width=True)
            # st.write(busy_day)

        with col2:
            st.subheader("🔥 Most busy month")
            busy_month = helper.month_activity_map(selected_user, df)
            fig_month = px.bar(
                busy_month,
                x=busy_month.index,
                y=busy_month.values,
                color=busy_month.values,
                color_continuous_scale="inferno",
                text=busy_month.values,
                title="Most Active Months",
            )
            fig_month.update_traces(textposition="outside", marker_line_color="white", marker_line_width=1.5)
            fig_month.update_layout(
                plot_bgcolor="#0E1117",
                paper_bgcolor="#0E1117",
                font_color="white",
                title_font_size=18,
                title_x=0.5,
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=False),
            )
            st.plotly_chart(fig_month, use_container_width=True)

        # headmap of user activity
        st.title("Weekly Activity Map")
        user_heatmap = helper.activity_heatmap(selected_user, df)
        fig, ax = plt.subplots()
        ax = sns.heatmap(user_heatmap)
        st.pyplot(fig)

        # finding the busiest person in the group
        if selected_user == "Overall":
            st.title("Most Busy Users")

            # Get data
            x, new_df = helper.most_busy_user(df)

            # Create figure
            fig, ax = plt.subplots(figsize=(10, 7))

            # Gradient colors
            colors = plt.cm.viridis(np.linspace(0.3, 0.8, len(x)))

            # Create columns
            col1, col2 = st.columns(2)

            with col1:
                bars = ax.bar(x.index, x.values, color=colors, edgecolor='white', linewidth=1.5)

                # Add value labels on top
                for bar in bars:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width() / 2, height + 0.1, str(int(height)),
                            ha='center', va='bottom', fontsize=10, fontweight='bold', color='white')

                # Rotate x-axis labels
                plt.xticks(rotation=45, ha='right', fontsize=10, fontweight='bold', color='white')

                # Dark theme styling
                ax.set_facecolor('#0E1117')
                fig.patch.set_facecolor('#0E1117')
                ax.tick_params(colors='white')
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.spines['left'].set_color('white')
                ax.spines['bottom'].set_color('white')

                # Optional subtle grid
                ax.yaxis.grid(True, linestyle='--', alpha=0.3, color='white')

                st.pyplot(fig)

            with col2:
                st.dataframe(new_df)


        # word cloud
        st.title("Word Cloud! ☁️️")

        df_wc = helper.create_wordcloud(selected_user, df)

        # Create a smaller, compact figure
        fig, ax = plt.subplots(figsize=(3, 3), dpi=150)  # very small and sharp
        ax.imshow(df_wc, interpolation="bilinear")
        ax.axis("off")

        # Optional: match dark theme background
        fig.patch.set_facecolor("#0E1117")
        ax.set_facecolor("#0E1117")

        # Tight layout to remove extra padding
        plt.tight_layout(pad=0)

        # Display compactly without stretching
        st.pyplot(fig, use_container_width=False)

        # most common df
        most_common_df = helper.most_common_words(selected_user, df)
        most_common_df.columns = ['word', 'count']  # Ensure proper column names

        # Create a modern horizontal bar chart
        fig = px.bar(
            most_common_df,
            x='count',
            y='word',
            orientation='h',
            title='Most Common Words',
            color='count',
            color_continuous_scale='turbo',  # Try 'plasma', 'magma', 'turbo' for variety
            height=600
        )

        # Reverse the y-axis to show highest count at the top
        fig.update_layout(
            yaxis=dict(autorange="reversed"),
            title_font=dict(size=24),
            font=dict(size=14),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        # Display in Streamlit
        st.title("🌈 Most Common Words")
        st.plotly_chart(fig, use_container_width=True)

        # emoji analysis
        emoji_df = helper.emoji_helper(selected_user, df)

        st.title("Most Used Emojis")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Emoji DataFrame")
            st.dataframe(emoji_df, use_container_width=True)

        fig = px.bar(
            emoji_df,
            x='Count',
            y='Emoji',
            orientation='h',
            text='Count',
            color='Count',
            color_continuous_scale='Oranges'
        )
        fig.update_layout(yaxis={'categoryorder': 'total ascending'})

        with col2:
            st.subheader("Emoji Bar Chart")
            st.plotly_chart(fig, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            # monthly timeline
            st.title("Monthly Timeline")
            timeline = helper.monthly_timeline(selected_user, df)
            fig, ax = plt.subplots()
            ax.plot(timeline['time'], timeline['message'], color='green')
            plt.xticks(rotation=45, ha='right')
            st.pyplot(fig)

        with col2:
            # daily timeline
            st.title("Daily Timeline")
            daily_timeline = helper.daily_timeline(selected_user, df)
            fig, ax = plt.subplots()
            ax.plot(daily_timeline['only_date'], daily_timeline['message'], color='white')
            plt.xticks(rotation=45, ha='right')
            st.pyplot(fig)
            # st.dataframe(daily_timeline)





