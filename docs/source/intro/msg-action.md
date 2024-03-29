# 消息行为操作

```{admonition} 相关知识
:class: note
如果你不知道什么是“行为”和“行为操作”，建议先浏览：[行为的相关知识](../references/event-action)
```

消息行为操作作为 melobot 中最主要的行为操作，十分常用。

## 单条消息的构造

```{admonition} 相关知识
:class: note
如果你不知道单条消息的表示方式，有“cq 字符串”和“消息段”两种格式，建议先浏览：[消息内容的数据结构](../references/msg)
```

一般来说，发送纯文本内容是最普遍的，方法也十分简单：

```python
await send("你好啊")
```

如果要发送多媒体内容，首先要通过各自的构造函数构造**消息段对象**，然后直接传入 {func}`.send` 作为参数。

例如使用 {func}`.image_msg` 构造图片内容：

```python
# 获得“图片内容”的消息段对象
img = image_msg("https://www.glowmem.com/static/avatar.jpg")
await send(img)
```

其他多媒体消息构造函数，及这些函数的参数，参考：[消息构造函数](#cq-msgs)

单条消息中，自然可能有多种类型的内容同时存在。此时这样处理：

```python
# 例如文本内容和图片内容同时存在：
await send([
    # text_msg 可从 melobot.models 导入，也是消息构造函数之一
    text_msg("给你分享一张图片哦，这是 melobot 项目作者的头像"),
    image_msg("https://www.glowmem.com/static/avatar.jpg")
])
```

## 自定义消息内容的构造

一般来说，melobot 自带的消息构造函数已足够使用。但是某些 OneBot 实现程序，可能会支持某些自定义的消息内容，**这些自定义消息内容，是 OneBot 标准中没有的，也不被 melobot 所直接支持**。

这时你可以使用 {func}`.custom_type_msg` 来构造**自定义消息段对象**。

例如在知名 OneBot 实现项目 [OpenShamrock](https://github.com/whitechi73/OpenShamrock) 中，存在一种自定义的消息内容 [touch 消息](https://whitechi73.github.io/OpenShamrock/message/special.html#%E6%88%B3%E4%B8%80%E6%88%B3-%E5%8F%8C%E5%87%BB%E5%A4%B4%E5%83%8F)（戳一戳，双击头像）。对应的消息段数据结构如下：

```json
{
    "type": "touch",
    "data": {
        "id": "1574260633"
    }
}
```

如何让 melobot 发送这种自定义的消息内容？非常简单：

```python
touch = custom_type_msg("touch", {"id": "1574260633"})
await send(touch)

# 或者再自行封装一下 :)
from functools import partial
def touch_msg(uid: int):
    return custom_type_msg("touch", {"id": str(uid)})
await send(touch_msg(1574260633))
```

## 单条消息的发送方法

{func}`.send` 可根据当前触发事件，自动定位要向何处发送消息。如果想要自定义发送目标，也很容易。只需要将{func}`.send` 换成 {func}`.send_custom_msg` 即可，它的第一参数与 {func}`.send` 完全相同。

```python
# 发送一个自定义目标的私聊消息，userId 为 qq 号
await send_custom_msg(..., isPrivate=True, userId=1574260633)
# 发送一个自定义目标的群聊消息，groupId 为群号
await send_custom_msg(..., isPrivate=False, groupId=535705163)
```

如果要回复触发消息事件处理方法的那条消息，按照之前学到的，应该这样做：

```python
@plugin.on_start_match(".hello")
async def say_hi() -> None:
    e = msg_event()
    # reply_msg 可从 melobot.models 导入，也是消息构造函数之一
    await send([
        reply_msg(e.id),
        text_msg("你好哇")
    ])
```

这样是十分繁琐的，但是“发送回复消息”这一行为也很普遍。使用 {func}`.send_reply` 简化：

```python
@plugin.on_start_match(".hello")
async def say_hi() -> None:
    # send_reply 第一参数与 send 完全相同
    await send_reply("你好哇")
```

想要提前结束事件处理方法，一般会用 `return`：

```python
@plugin.on_start_match(".hello")
async def say_hi() -> None:
    if msg_event().sender.id != 1574260633:
        await send("你好~ 你不是我的主人哦")
        return
    # 接下来是机器人主人的处理逻辑
    await send(">w<")
    await send("主人好")
```

用 {func}`.finish` 可以把 `return` 简化掉：

```python
# 就目前我们掌握的知识来看，可以认为 finish 等价于以下代码：
await send(...)
return

# 刚才的代码，使用 finish 优化后
@plugin.on_start_match(".hello")
async def say_hi() -> None:
    if msg_event().sender.id != 1574260633:
        # finish 运行完就返回啦，不需要显式 return
        await finish("你好~ 你不是我的主人哦")
    await send(">w<")
    await send("主人好")
```

同理，{func}`.send_reply` 对应的优化版本是：{func}`.reply_finish`。使用方法和特征与 {func}`.finish` 类似。但是它发送的是回复消息。

## 转发消息的构造

```{admonition} 相关知识
:class: note
如果你不知道转发消息的表示，主要依托于消息结点，建议先浏览：[转发消息与消息结点](../references/forward-msg.md)
```

一个消息结点，实际上承载了之前提到的“单条消息”的所有内容。因此，它实际上是“单条消息”的等价表达。发送单条消息时，由于是一条一条发送的，因此不需要引入“消息结点”这个概念。

但是如果发送的是转发消息，由于转发消息是多个“单条消息”的汇总，因此便需要“消息结点”这一概念，用于描述转发消息中的单条消息。所以在 melobot 中，**转发消息中的单条消息是一个消息结点，转发消息本身是消息结点的列表**。

很自然地，构造转发消息的第一步，是**构造消息结点**。

构造“合并转发结点”，使用 {func}`.refer_msg_node` 函数：

```python
# 这里的 msg_id 是已存在的消息的 id
# 可通过消息事件的 id 属性获得，或通过 get_forward_msg 行为操作的响应获得
refer_node = refer_msg_node(msg_id)
```

构造“合并转发自定义结点”，使用 {func}`.custom_msg_node` 函数：

```python
# 第一参数是消息内容，与上述单条消息的发送方法的第一参数相同
# 后续参数用于表示，在转发消息中显示的 发送人昵称 和 发送人的qq号（int 类型）
node1 = custom_msg_node("你好", sendName="机器人", sendId=xxxxxx)

node2 = custom_msg_node(image_msg(...),
                        sendName="机器人",
                        sendId=xxxxxx)

node3 = custom_msg_node([text_msg(...), image_msg(...)],
                        sendName="机器人",
                        sendId=xxxxxx)
```

将消息结点组成列表，实际上就是“一条转发消息”的等价表达了，使用 {func}`.send_forward` 来发送它：

```python
await send_forward([refer_node, node1, node2, node3])
```

## 转发消息的发送方法

{func}`.send_forward` 可根据当前触发事件，自动定位要向何处发送消息。同理，要自定义发送目标，将{func}`.send_forward` 换成 {func}`.send_custom_forward` 即可，它的第一参数与 {func}`.send_forward` 完全相同。

```python
# 发送一个自定义目标的私聊消息，userId 为 qq 号
await send_custom_forward(..., isPrivate=True, userId=1574260633)
# 发送一个自定义目标的群聊消息，groupId 为群号
await send_custom_forward(..., isPrivate=False, groupId=535705163)
```

## 总结

本篇主要说明了如何构造和发送各种消息。

下一篇将重点说明：如何实现其他行为操作与行为操作的响应。