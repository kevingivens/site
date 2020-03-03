Title: Parsing ITCH Messages in C++
Date: 2020-02-20 12:20
Category: Finance
Tags: C++, Trading

Summary: We review how to parse ITCH messages in C++ with configurable code

*Introduction*

The ITCH protocol is a message protocol used for trading on the NASDAQ stock exchange.
In this post, I wanted to review how to parse ITCH messages in C++.  As always, you
can find my sample code to go along with this post on my github [page](https://github.com/kevingivens/blog).


Essentially, the ITCH protocol is a binary message format for placing orders on NASDAQ.
The latest version of protocol is 5.0 and its spec can be found [here](https://www.nasdaqtrader.com/content/technicalsupport/specifications/dataproducts/NQTVITCHspecification.pdf) ITCH defines a series of messages along
with the type and size of the message's components.  

For example, an Add order looks like this:


### Add Order Message

|Name                   | Offset | Length | Value | Notes|
|---------------------- |-----|----------|--------|------|
|Message Type           |   0 |1 |“A” |Add Order – No MPID Attribution Message.|
|Stock Locate           |   1 |2 |Integer| Locate code identifying the security|
|Tracking Number        |   3 | 2 |Integer | Nasdaq internal tracking number|
|Timestamp              |   5   | 6 |Integer | Nanoseconds since midnight.|
|Order Reference Number |  11   | 8 |Integer | Unique reference number assigned to new order at the time of receipt.|
|Buy/Sell Indicator     |19 |1  |Alpha| The type of order being added. “B” = Buy “S” = Sell|
|Shares                 |20 |4  |Integer | The total number of shares associated with the order being added to the book.|
|Stock                  |24 |8  |Alpha |Stock symbol, right padded with spaces|
|Price                  |32 |4  |Price | The display price of the new order|



The job of the parser is to read these messages from a file (or a file descriptor)
and to translate them into objects (classes in C++) that a program can understand.
For instance, a C++ struct that represents an add order could look like this

```cpp
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

### Implementation

There are many ways to write a message parser in C++.  Searching on github shows
several different ITCH messages parsers all taking somewhat different approaches.
The one I liked the most and decided to base my implementation on is this
[one](https://github.com/mbergin/asx24itch).  It's actually a ITCH parser for the
Australian Stock Exchange.  I just adapted it to NASDAQ.

At the core of any parser is a hierarchy of types and a switch statement handling
each type. In the ITCH parser, this switch looks like the following:



```cpp
switch (MessageType(msg[0])) {
case MessageType::SystemEvent:
    return parseAs<SystemEvent>(msg, len, std::forward<Handler>(handler));
case MessageType::StockDirectory:
    return parseAs<StockDirectory>(msg, len, std::forward<Handler>(handler));        
case MessageType::StockTradingAction:
    return parseAs<StockTradingAction>(msg, len, std::forward<Handler>(handler));

    ...

default:
    return ParseStatus::UnknownMessageType;
}
```

the `parseAs` function converts the raw bytes into message structs.  It does so using the following three lines in it's function body.

```
MsgType msg{*reinterpret_cast<const MsgType*>(buf)};
network_to_host(msg);
handler(msg);
```

It's worth looking at each one of these in detail.

The first line

```
MsgType msg{*reinterpret_cast<const MsgType*>(buf)};
```
use reinterpret_cast to cast the bytes into the appropriate struct. This casting
succeeds because the message structs are declared as packed in the message
header file, e.g

```cpp
#pragma pack(push, 1)

  struct SystemEvent {
     MessageType message_type;
     uint16_t stock_locate;
     uint16_t tracking_number;
     TimeStamp time_stamp;
     EventCode event_code;
  };

#pragma pack(pop)
```

This means that the data members are aligned to match the message bytes.  For more on alignment and packing, see this stackoverflow thread. (https://stackoverflow.com/questions/3318410/pragma-pack-effect)

There is a drawback to this approach. Namely, #pragma push is not supported by all C++ compilers and therefor limits the portability of the code.  It's a fare point, but for the purpose of this exercise I choose to use #pragma push because it simplifies the casting from bytes to structs.  

There is another issue about portability I need to discuss.  That's the byte swapping function

```cpp
network_to_host(msg);
```

The message are in Big Endian format (network) and my system (host) is Little Endian (x86).  The `network_to_host` functions simply reverse the byte order.  There are OS specific utilities for doing this (e.g. in Linux), but that would again limit code portability (a common problem in C++!)

The final step in the parse function   

```cpp
handler(msg);
```


This is a generic method meant to redirect the messages to some destination.  In this example it's print function.  It could in principle redirect to some other location such as a data base or an in-memory data structure representing a Limit Order Book.
