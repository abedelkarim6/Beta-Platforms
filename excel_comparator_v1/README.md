# Excel-comparator

## Usage steps

1. Run this command:
```
pip install -r requirements.txt

- Note that in windows you have to run this command:
pip install python-magic-bin
```

2. Run this command:
```
streamlit run app.py
```


## Matching logic


### **Given Data**
Given 1 excel sheet that includes 4 columns, each 2 represents a dataset, the structure is as follows:

sender_name_1 | amount_1 | sender_name_2 | amount_2 | 

### **Goal**: 
1. To find all non-matched rows between the datasets.
2. To find all potential-matched rows between the datasets. Where a potential match is exact match in amount AND 80% similarity in name.

### **Matching Logic**
We have 2 matching Logic layers:

#### **Logic 1:**
1. Iterate over all rows of df1 and df2, when amount matches.
2. Go check strings that are exactly same names. 
OR
3. Incase of 2 words: to find all substrings of minimum-length=3 that exactly match.

#### **Logic 2:**
1. Iterate over all rows of df1 and df2, when amount matches.
2. Go check all sub-strings that are words that are at least 80% similar. 


### Output 
1. non-matching rows.
2. potential matching rows