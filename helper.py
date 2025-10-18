from urlextract import URLExtract
import matplotlib.pyplot as plt
extract = URLExtract()
from wordcloud import WordCloud
import  pandas as pd
from collections import Counter
import re
import emoji

def fetch_stats(selected_user, df):
    if(selected_user !=  "Overall"):
        df = df[df['user'] == selected_user]
    # 1 fetch no of messages
    num_messages = df.shape[0]

    # 2 fetch no of words
    words = []
    for msg in df['message']:
        words.extend(msg.split())

    # 3 num of media messages
    num_media_messages = df[df['message'] == '<Media omitted>\n'].shape[0]

    # 4 find the num of links
    links = []
    for msg in df['message']:
        links.extend(extract.find_urls(msg))

    return num_messages, len(words), num_media_messages, len(links)

def most_busy_user(df):
    x = df['user'].value_counts().head()
    df = (df['user'].value_counts() / df.shape[0] * 100).round(2).reset_index().rename(columns={"user" : "name", "count" : "percent"})
    return x, df


# def create_wordcloud(selected_user, df):
#     if (selected_user != "Overall"):
#         df = df[df['user'] == selected_user]
#     wc = WordCloud(width=500, height=500, min_font_size=10,background_color="white")
#     df_wc = wc.generate(df["message"].str.cat(sep=" "))
#     return df_wc
def create_wordcloud(selected_user, df):
    import re
    from wordcloud import WordCloud

    # Read stop words
    with open('stop_hinglish.txt', 'r', encoding='utf-8') as f:
        stop_words = f.read().splitlines()

    # Filter for specific user
    if selected_user != "Overall":
        df = df[df['user'] == selected_user]

    # Remove unwanted system messages
    temp = df[df['user'] != 'group_notification']
    temp = temp[~temp['message'].str.contains('<Media omitted>', case=False, na=False)]
    temp['message'] = temp['message'].str.replace('<This message was edited>', '', regex=False)
    temp = temp[temp['message'].str.strip() != '']

    # Prepare all user name parts
    nusers = df['user'].unique().tolist()
    name_parts = []
    for name in nusers:
        for part in re.findall(r'\w+', name.lower()):
            name_parts.append(part)

    # Collect filtered words
    words = []
    for msg in temp['message']:
        for word in msg.lower().split():
            word = re.sub(r'[^a-zA-Z0-9@]', '', word)  # remove special chars except '@'
            if (
                word
                and not word.startswith('@')       # remove mentions
                and word not in stop_words          # remove stop words
                and word not in name_parts          # remove username parts
            ):
                words.append(word)

    # Generate word cloud from filtered words
    text = " ".join(words)
    wc = WordCloud(width=500, height=500, min_font_size=10, background_color="white").generate(text)

    return wc


def most_common_words(selected_user,df):

    f = open('stop_hinglish.txt','r')
    stop_words = f.read()

    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    temp = df[df['user'] != 'group_notification']
    temp = temp[temp['message'] != '<Media omitted>\n']
    temp['message'] = temp['message'].str.replace('<This message was edited>', '', regex=False)

    # Remove empty messages after cleanup
    temp = temp[temp['message'].str.strip() != '']

    nusers = df['user'].unique().tolist()
    name_parts = []
    for name in nusers:
        for part in re.findall(r'\w+', name.lower()):  # extract words from names
            name_parts.append(part)

    words = []
    for msg in temp['message']:
        for word in msg.lower().split():
            word = re.sub(r'[^a-zA-Z0-9@]', '', word)  # remove special chars but keep '@' to check
            # exclude stopwords, usernames, and mentions
            if (
                    word  # not empty
                    and not word.startswith('@')  # ignore mentions like @Hunter
                    and word not in stop_words  # ignore stop words
                    and word not in name_parts  # ignore usernames
            ):
                words.append(word)

    most_common_df = pd.DataFrame(Counter(words).most_common(20))
    return most_common_df

def emoji_helper(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]
    emojis = []
    for message in df['message']:
        emojis.extend([c for c in message if emoji.is_emoji(c)])  # works with emoji v2+

    emoji_df = pd.DataFrame(Counter(emojis).most_common(10), columns=['Emoji', 'Count'])
    return emoji_df

# monthly timeline
def monthly_timeline(selected_user,df):

    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    timeline = df.groupby(['year', 'month_num', 'month']).count()['message'].reset_index()

    time = []
    for i in range(timeline.shape[0]):
        time.append(timeline['month'][i] + "-" + str(timeline['year'][i]))

    timeline['time'] = time

    return timeline

def daily_timeline(selected_user,df):

    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    daily_timeline = df.groupby('only_date').count()['message'].reset_index()

    return daily_timeline

def week_activity_map(selected_user,df):

    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    return df['day_name'].value_counts()

def month_activity_map(selected_user,df):

    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    return df['month'].value_counts()

def activity_heatmap(selected_user,df):

    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    user_heatmap = df.pivot_table(index='day_name', columns='period', values='message', aggfunc='count').fillna(0)

    return user_heatmap
