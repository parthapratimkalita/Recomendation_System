import pandas as pd 
import numpy as np
import matplotlib.pyplot as plt

def main():
    df = pd.read_csv('movies.csv')


    df1 = pd.read_csv('ratings.csv')


    df2 = pd.read_csv('links.csv')


    df3 = pd.read_csv('tags.csv')
    df3 = df3.drop(['userId', 'timestamp'], axis=1)
    df3 = df3.groupby('movieId').agg({'tag': lambda x: list(set(x))}).reset_index()


    gk = df1.groupby('movieId')
 

    df_ratings = df1.groupby('movieId').agg({'userId': lambda x: list(x), 'rating': lambda x: list(x)}).reset_index()

    
    for i in df_ratings.userId:
        for j in range(len(i)):
            for k in range(j+1, len(i)):
                if i[j] == i[k]:
                    print('Duplicate')
                    break


    

    temp = []
    for i in range(len(df_ratings.rating)):
        temp.append(len(df_ratings.rating[i]))
    df_ratings['no_of_total_ratings'] = temp


    for i in range(len(df_ratings.no_of_total_ratings)):
        if df_ratings.no_of_total_ratings[i] ==0:
            print('Error')
            print(i)
            break


    dfRatings_filter = df_ratings.drop(['userId'], axis=1)

    

    temp = []
    for i in range(len(dfRatings_filter.rating)):
        temp.append(sum(dfRatings_filter.rating[i])/len(dfRatings_filter.rating[i]))
    dfRatings_filter['avg_rating'] = temp

    

    infered_temp_data_frame = df.merge(dfRatings_filter, on='movieId', how='left').merge(df3, on='movieId', how='left')
    infered_temp_data_frame = infered_temp_data_frame[['movieId', 'title', 'genres','tag', 'rating', 'no_of_total_ratings',]]
    infered_temp_data_frame.to_json('infered_temp_data_frame.json', orient='records')
    infered_temp_data_frame.to_csv('infered_temp_data_frame.csv', index=False)
    
    temp = []
    for i in infered_temp_data_frame.genres:
        temp.append(i.split('|'))
    infered_temp_data_frame['genres'] = temp
    

    print('infered_temp_data_frame.head()')
    print(infered_temp_data_frame[['movieId', 'genres','tag', 'rating',]].tail())
    print('infered_temp_data_frame.shape')
    print(infered_temp_data_frame.shape)

    C= dfRatings_filter['avg_rating'].mean()

    m= dfRatings_filter['no_of_total_ratings'].quantile(0.9)
    
    q_movies = dfRatings_filter.copy().loc[dfRatings_filter['no_of_total_ratings'] >= m]
    print(q_movies.head())


    def weighted_rating(x, m=m, C=C):
        v = x['no_of_total_ratings']
        R = x['avg_rating']
        # Calculation based on the IMDB formula
        return (v/(v+m) * R) + (m/(m+v) * C)
    
    q_movies['score'] = q_movies.apply(weighted_rating, axis=1)
    q_movies = q_movies.sort_values('score', ascending=False)

    df_merged = q_movies.merge(df, on='movieId', how= 'left')
    df_merged = df_merged[['movieId', 'title', 'genres', 'no_of_total_ratings', 'avg_rating', 'score']]
    df_merged.to_json('df_merged.json', orient='records')

    

    print(df_merged.head(20))

    def content_based_filtering(gener_list, df):

        df = df.copy()
        movies = []
        for i in gener_list:
            for j in range(len(df.genres)):
                if i in df.genres[j]:
                    movies.append(df.movieId[j])
        movies = list(set(movies))
        filtered_df = df[df['movieId'].isin(movies)]
        filtered_df.to_json('content_filtered.json', orient='records')
        print(filtered_df.head(20))

    movies = ['Comedy', 'Romance']
    content_based_filtering(movies, df_merged)


if __name__ == '__main__':
    main()