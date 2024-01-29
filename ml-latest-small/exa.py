def main():
    # ... your existing code ...

    string = [1,1,4,5,6,7,9]

    for i in string:
        print(lambda sum: sum + i)
    split_string = string.split(',')

    print(split_string)

if __name__ == '__main__':
    main()