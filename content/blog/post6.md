Title: Parsing ITCH Messages in C++
Date: 2020-02-20 12:20
Category: Finance
Tags: C++, Trading

Summary: We review how to parse ITCH messages in C++ with configurable code


The ITCH protocol is a message protocol used for communicating with the NASDAQ stock exchange.
In this post, I wanted to review how to parse ITCH messages in C++. As always, you can find my sample code to go along with this post on my github [page](https://github.com/kevingivens/blog).


The latest version of protocol is 5.0 and its spec can be found [here](https://www.nasdaqtrader.com/content/technicalsupport/specifications/dataproducts/NQTVITCHspecification.pdf). ITCH defines a series of messages along with the type and size of each of the message's components.  

For example, an Add order looks like this:


**Add Order Message**

|Name                   | Offset | Length | Value  | Notes|
|---------------------- |--------|--------|--------|------|
|Message Type           |   0    | 1      |“A”     | Add Order – No MPID Attribution Message.|
|Stock Locate           |   1    | 2      |Integer | Locate code identifying the security|
|Tracking Number        |   3    | 2      |Integer | Nasdaq internal tracking number|
|Timestamp              |   5    | 6      |Integer | Nanoseconds since midnight.|
|Order Reference Number |   11   | 8      |Integer | Unique reference number assigned to new order at the time of receipt.|
|Buy/Sell Indicator     |   19   | 1      |Alpha   | The type of order being added. “B” = Buy “S” = Sell|
|Shares                 |   20   | 4      |Integer | The total number of shares associated with the order being added to the book.|
|Stock                  |   24   | 8      |Alpha   | Stock symbol, right padded with spaces|
|Price                  |   32   | 4      |Price   | The display price of the new order|


An example add order might look like this

```cpp
const char msg[] = {
        'S',                                            // messageType: SystemEvent
        '\xFF', '\xEE',                                 // uint16_t stock_locate: 65518
        '\xFF', '\xEE',                                 // uint16_t tracking_number: 65518
        '\xFF', '\xEE', '\xEE', '\xAA', '\x01', '\x02', // TimeStamp time_stamp: 65518
        'Q'                                             // EventCode: MarketStart
    };
```


The job of the parser is to read these messages from a file (or a file descriptor like a socket) and to translate them into objects (classes in C++) that a program can understand. For instance, a C++ struct that represents an add order could look like this

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

There are many ways to write a message parser in C++.  Searching on github shows several different ITCH messages parsers all taking somewhat different approaches. The one I liked the most and decided to base my implementation on is this [one](https://github.com/mbergin/asx24itch). It's actually a ITCH parser for the Australian Stock Exchange.  I just adapted it to NASDAQ.

At the core of the parser is a hierarchy of types and a switch statement handling each type. For the ITCH parser, this switch looks like the following:



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

The `parseAs` function converts the raw bytes into message structs.  It does so using the following three lines in it's function body.

```cpp
MsgType msg{*reinterpret_cast<const MsgType*>(buf)};
network_to_host(msg);
handler(msg);
```

It's worth looking at each one of these in detail.

The first line

```cpp
MsgType msg{*reinterpret_cast<const MsgType*>(buf)};
```
use reinterpret_cast to cast the bytes into the appropriate struct. This casting succeeds because the message structs are declared as packed in the message header file, e.g

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

This means that the data members are aligned to match the message bytes, i.e. there is no byte padding between data members.  For more on alignment and packing, see this stackoverflow thread. (https://stackoverflow.com/questions/3318410/pragma-pack-effect)

There is a drawback to this approach. Namely, #pragma push is not supported by all C++ compilers.  This limits the portability of the code.  It's a fair point, but for the purpose of this exercise I choose to use #pragma push because it simplifies the casting from bytes to structs.  Otherwise I would be forced to specify exactly how many bytes to read and in what order for each message type.  

There is another issue about portability I need to discuss.  That's the byte swapping function

```cpp
network_to_host(msg);
```

The incoming messages are in Big Endian (network) format. My system (host) is Little Endian (x86).  The `network_to_host` functions simply reverse the byte order. There are OS specific utilities for doing this (e.g. in Linux), but that would again limit code portability (a common problem in C++!).

For simplicity, I use the explicit byte swapping routines from the swap.hpp file such as

For instance
```cpp
template <>
inline void network_to_host(uint16_t& x)
{
    x = (x & 0x00FF) << 8 |
        (x & 0xFF00) >> 8;
}

template <>
inline void network_to_host(uint32_t& x)
{
    x = (x & 0x000000FF) << 24 |
        (x & 0x0000FF00) << 8 |
        (x & 0x00FF0000) >> 8 |
        (x & 0xFF000000) >> 24;
}
```

Each message is then swapped by an appropriate function, for instance

```cpp
template<>
  inline void network_to_host<SystemEvent>(SystemEvent& msg) {
    network_to_host(msg.message_type);
    network_to_host(msg.stock_locate);
    network_to_host(msg.tracking_number);
    parse_ts(msg.time_stamp);
    network_to_host(msg.event_code);
  }
```

Each struct field is mapped to the correct `network_to_host` function via C++'s template pattern matching functionality.  The time stamp requires special treatment. We'll this topic discuss below.


The final step in the parse function

```cpp
handler(msg);
```

This is a generic method meant to redirect the messages to some destination. In this example it's a print function.  It could in principle redirect to some other location such as a data base or an in-memory data structure representing a Limit Order Book.


## The Trouble with TimeStamps

Keen readers will notice an annoying little wrinkle in the type hierarchy. Namely the TimeStamp field, which is present in all messages, is *6 bytes* long. This is natural in the sense that it's enough bytes to cover the number of nanoseconds in a day.  It's unnatural in the sense that there are no built-in *6 byte* type in C++.

To handle this situation we declare the TimeStamp to be a *6 bytes* array

```cpp
struct TimeStamp {
     uint8_t data[6];
};
```     

This ensures that when the message structs are initialized via the reinterpret_cast, the correct number of bytes are read from the file.

However, when we swipe the bytes, we take the opportunity to upcast this 6 byte array an 8 byte int (uint64_t) via the following function

```cpp
uint64_t parse_ts(char* a){
     return (
         (static_cast<uint64_t>(bswap_16(*(reinterpret_cast<uint16_t *>(a)))) << 32) |
            static_cast<uint64_t>(bswap_32(*(reinterpret_cast<uint32_t *>(a+2))))
      );
 }
```  

## Life's easier with Python

With the struct-casting, byte-swapping and printing functions in place, the parser is functional (barely).  The next step ensure they work for all message types from the ITCH specification.  

Personally, I found this task tedious and error prone.  Instead, I copied the spec into a yaml file and wrote a python program that parsers the yaml file and builds the structs, byte-swapping functions and printers in C++.  This approach has the nice advantage that when the ITCH stand changes, the C++ parser can easily be built again from the specification file.

An example entry from the yaml ITCH specification file looks like the following

```yaml
name: AddOrder
type: Message
MessageType:           [1,  “A”,     Add Order – No MPID Attribution Message.]
StockLocate:           [2,  Integer, Locate code identifying the security]
TrackingNumber:        [2,  Integer, Nasdaq internal tracking number]
Timestamp:             [6,  Integer, Nanoseconds since midnight.]
OrderReferenceNumber:  [8,  Integer, The unique reference number assigned to the new order at the time of receipt.]
BuySellIndicator:      [1,  Alpha,   The type of order being added.]
Shares:                [4,  Integer, The total number of shares associated with the order being added to the book.]
Stock:                 [8,  Alpha,   Stock symbol, right padded with spaces]
Price:                 [4,  Price,  The display price of the new order. Refer to Data Types for field processing notes.]
---
name: BuySellIndicator
type: Enum
Buy:  [“B”, Buy Order.]
Sell: [“S”, Sell Order.]
```
The python program consists of a series of yaml parsers, each one generating a different C++ file needed for the parser.

As always, you can find code for this blog on my github page.  See you next time.
