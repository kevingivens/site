Title: Parsing ITCH Messages in C++
Date: 2020-02-20 12:20
Category: Finance
Tags: C++, Trading

Summary: We review how to parse ITCH messages in C++ with configurable code

# Introduction

The ITCH protocol is a message protocol used for trading on the NASDAQ stock exchange.
In this post, I wanted to review how to parse ITCH messages in C++.  As always, you
can find my sample code to go along with this post on my github [page](https://github.com/kevingivens/blog).


Essentially, the ITCH protocol is a binary message format for placing orders on NASDAQ.
The latest version of protocol is 5.0 and its spec can be found [here](https://www.nasdaqtrader.com/content/technicalsupport/specifications/dataproducts/NQTVITCHspecification.pdf) ITCH defines a series of messages along with the type and size of the message's components.  For example, an ADD order looks like this

### Add Order Message

|Name | Offset | Length | Value | Notes|
|-----|:------:|:------:|:-----:|------|
|Message Type| 0 |1 |“A” |Add Order – No MPID Attribution Message.|
|Stock Locate| 1 |2 |Integer| Locate code identifying the security|
|Tracking Number| 3| 2 |Integer | Nasdaq internal tracking number|
|Timestamp |5| 6 |Integer | Nanoseconds since midnight.|
|Order Reference Number |11 |8 |Integer | The unique reference number assigned to the new order at the time of receipt.|
|Buy/Sell Indicator| 19 |1 |Alpha| The type of order being added. “B” = Buy Order. “S” = SellOrder.|
|Shares |20 |4 |Integer | The total number of shares associated with the order being added to the book.|
|Stock |24 |8 |Alpha |Stock symbol, right padded with spaces|
|Price |32 |4 |Price (4)| The display price of the new order. Refer to Data Types for field processing notes.|


The job of the parser is to read these messages from a file (or a file descriptor)
and to translate them into objects (classes in C++) that a program can understand.
For instance, a C++ struct that represents an add order could look like this

```c++
struct AddMessage {
  MessageType message_type;
  uint16_t stock_locate;
  uint16_t tracking_number;
  TimeStamp time_stamp;
  uint64_t order_ref_num;
  BuySell buy_sell;
  uint32_t shares;
  char stock[8];
  uint32_t price;
}


```

## Implementation

There are many ways to write a message parser in C++.  Searching on github shows
several different ITCH messages parsers all taking somewhat different approaches.
The one I liked the most and decided to base my implementation on is [this one](https://github.com/mbergin/asx24itch)  It's actually a ITCH parser for the Australian Stock
Exchange.  I just adapted it to NASDAQ.   