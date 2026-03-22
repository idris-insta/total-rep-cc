import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { ScrollArea } from '../components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSeparator } from '../components/ui/dropdown-menu';
import { 
  MessageSquare, Send, Plus, Users, Search, Paperclip, Image, 
  MoreVertical, Check, CheckCheck, Clock, Star, Pin, Smile,
  UserPlus, Settings, Phone, Video, FileText, ListTodo,
  Calendar, Flag, X, ChevronRight
} from 'lucide-react';
import api from '../lib/api';
import { toast } from 'sonner';
import { useAuth } from '../context/AuthContext';

const Chat = () => {
  const { user } = useAuth();
  const [conversations, setConversations] = useState([]);
  const [selectedChat, setSelectedChat] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [users, setUsers] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showNewChat, setShowNewChat] = useState(false);
  const [showNewGroup, setShowNewGroup] = useState(false);
  const [showTaskDialog, setShowTaskDialog] = useState(false);
  const [activeTab, setActiveTab] = useState('chats');
  const messagesEndRef = useRef(null);
  const pollingRef = useRef(null);
  
  const [newGroup, setNewGroup] = useState({ name: '', description: '', member_ids: [] });
  const [newTask, setNewTask] = useState({ title: '', description: '', assigned_to: '', due_date: '', priority: 'medium' });

  useEffect(() => {
    fetchConversations();
    fetchUsers();
    fetchTasks();
    
    // Polling for new messages every 5 seconds
    pollingRef.current = setInterval(() => {
      fetchConversations();
      if (selectedChat) {
        fetchMessages(selectedChat);
      }
    }, 5000);
    
    return () => clearInterval(pollingRef.current);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const fetchConversations = async () => {
    try {
      const res = await api.get('/chat/conversations');
      setConversations(res.data);
    } catch (err) {
      console.error('Failed to fetch conversations', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchUsers = async () => {
    try {
      const res = await api.get('/chat/users');
      setUsers(res.data);
    } catch (err) {
      console.error('Failed to fetch users', err);
    }
  };

  const fetchTasks = async () => {
    try {
      const res = await api.get('/chat/tasks');
      setTasks(res.data);
    } catch (err) {
      console.error('Failed to fetch tasks', err);
    }
  };

  const fetchMessages = useCallback(async (chat) => {
    if (!chat) return;
    try {
      const endpoint = chat.type === 'dm' 
        ? `/chat/messages/dm/${chat.id}`
        : `/chat/messages/group/${chat.id}`;
      const res = await api.get(endpoint);
      setMessages(res.data.messages || []);
    } catch (err) {
      console.error('Failed to fetch messages', err);
    }
  }, []);

  const selectChat = (chat) => {
    setSelectedChat(chat);
    fetchMessages(chat);
  };

  const sendMessage = async (e) => {
    e?.preventDefault();
    if (!newMessage.trim() || !selectedChat) return;
    
    try {
      const endpoint = selectedChat.type === 'dm'
        ? `/chat/messages/dm/${selectedChat.id}`
        : `/chat/messages/group/${selectedChat.id}`;
      
      await api.post(endpoint, { content: newMessage, message_type: 'text' });
      setNewMessage('');
      fetchMessages(selectedChat);
      fetchConversations();
    } catch (err) {
      toast.error('Failed to send message');
    }
  };

  const createGroup = async () => {
    if (!newGroup.name || newGroup.member_ids.length === 0) {
      toast.error('Please enter group name and select members');
      return;
    }
    try {
      const res = await api.post('/chat/groups', newGroup);
      toast.success('Group created!');
      setShowNewGroup(false);
      setNewGroup({ name: '', description: '', member_ids: [] });
      fetchConversations();
      selectChat({ type: 'group', id: res.data.id, name: res.data.name });
    } catch (err) {
      toast.error('Failed to create group');
    }
  };

  const createTask = async () => {
    if (!newTask.title || !newTask.assigned_to) {
      toast.error('Please enter task title and assignee');
      return;
    }
    try {
      await api.post('/chat/tasks', newTask);
      toast.success('Task created!');
      setShowTaskDialog(false);
      setNewTask({ title: '', description: '', assigned_to: '', due_date: '', priority: 'medium' });
      fetchTasks();
    } catch (err) {
      toast.error('Failed to create task');
    }
  };

  const updateTaskStatus = async (taskId, status) => {
    try {
      await api.put(`/chat/tasks/${taskId}?status=${status}`);
      fetchTasks();
      toast.success('Task updated!');
    } catch (err) {
      toast.error('Failed to update task');
    }
  };

  const startDM = (targetUser) => {
    setShowNewChat(false);
    selectChat({ type: 'dm', id: targetUser.id, name: targetUser.name || targetUser.email });
  };

  const formatTime = (dateStr) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const now = new Date();
    const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) {
      return date.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
    } else if (diffDays === 1) {
      return 'Yesterday';
    } else if (diffDays < 7) {
      return date.toLocaleDateString('en-IN', { weekday: 'short' });
    }
    return date.toLocaleDateString('en-IN', { day: '2-digit', month: 'short' });
  };

  const filteredConversations = conversations.filter(c => 
    c.name?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getInitials = (name) => {
    if (!name) return '?';
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  };

  return (
    <div className="h-[calc(100vh-120px)] flex gap-4" data-testid="chat-page">
      {/* Sidebar */}
      <div className="w-80 flex flex-col border rounded-lg bg-white shadow-sm">
        <div className="p-4 border-b">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-slate-900 font-manrope">Messages</h2>
            <div className="flex gap-2">
              <Dialog open={showNewChat} onOpenChange={setShowNewChat}>
                <DialogTrigger asChild>
                  <Button size="sm" variant="ghost"><MessageSquare className="h-4 w-4" /></Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader><DialogTitle>Start New Chat</DialogTitle></DialogHeader>
                  <ScrollArea className="h-80">
                    <div className="space-y-2">
                      {users.map(u => (
                        <div 
                          key={u.id} 
                          className="flex items-center gap-3 p-2 rounded hover:bg-slate-100 cursor-pointer"
                          onClick={() => startDM(u)}
                        >
                          <Avatar className="h-10 w-10">
                            <AvatarFallback className="bg-accent text-white">{getInitials(u.name)}</AvatarFallback>
                          </Avatar>
                          <div>
                            <p className="font-medium">{u.name || u.email}</p>
                            <p className="text-xs text-slate-500">{u.department || u.role}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                </DialogContent>
              </Dialog>
              
              <Dialog open={showNewGroup} onOpenChange={setShowNewGroup}>
                <DialogTrigger asChild>
                  <Button size="sm" variant="ghost"><Users className="h-4 w-4" /></Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader><DialogTitle>Create Group</DialogTitle></DialogHeader>
                  <div className="space-y-4">
                    <div>
                      <Label>Group Name</Label>
                      <Input value={newGroup.name} onChange={e => setNewGroup({...newGroup, name: e.target.value})} />
                    </div>
                    <div>
                      <Label>Description (optional)</Label>
                      <Input value={newGroup.description} onChange={e => setNewGroup({...newGroup, description: e.target.value})} />
                    </div>
                    <div>
                      <Label>Members</Label>
                      <div className="flex flex-wrap gap-1 mb-2">
                        {newGroup.member_ids.map(id => {
                          const u = users.find(x => x.id === id);
                          return (
                            <Badge key={id} variant="secondary" className="cursor-pointer" onClick={() => setNewGroup({...newGroup, member_ids: newGroup.member_ids.filter(x => x !== id)})}>
                              {u?.name || 'User'} ×
                            </Badge>
                          );
                        })}
                      </div>
                      <ScrollArea className="h-40 border rounded p-2">
                        {users.filter(u => !newGroup.member_ids.includes(u.id)).map(u => (
                          <div key={u.id} className="flex items-center gap-2 p-1 hover:bg-slate-100 cursor-pointer rounded" onClick={() => setNewGroup({...newGroup, member_ids: [...newGroup.member_ids, u.id]})}>
                            <Avatar className="h-6 w-6"><AvatarFallback className="text-xs">{getInitials(u.name)}</AvatarFallback></Avatar>
                            <span className="text-sm">{u.name || u.email}</span>
                          </div>
                        ))}
                      </ScrollArea>
                    </div>
                    <Button onClick={createGroup} className="w-full">Create Group</Button>
                  </div>
                </DialogContent>
              </Dialog>
            </div>
          </div>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <Input placeholder="Search..." className="pl-9" value={searchTerm} onChange={e => setSearchTerm(e.target.value)} />
          </div>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col">
          <TabsList className="grid w-full grid-cols-2 px-2">
            <TabsTrigger value="chats">Chats</TabsTrigger>
            <TabsTrigger value="tasks">Tasks</TabsTrigger>
          </TabsList>
          
          <TabsContent value="chats" className="flex-1 overflow-hidden m-0">
            <ScrollArea className="h-full">
              {filteredConversations.map(conv => (
                <div
                  key={`${conv.type}-${conv.id}`}
                  className={`flex items-center gap-3 p-3 cursor-pointer border-b hover:bg-slate-50 ${selectedChat?.id === conv.id ? 'bg-accent/10' : ''}`}
                  onClick={() => selectChat(conv)}
                >
                  <div className="relative">
                    <Avatar className="h-12 w-12">
                      <AvatarFallback className={conv.type === 'group' ? 'bg-purple-500 text-white' : 'bg-accent text-white'}>
                        {conv.type === 'group' ? <Users className="h-5 w-5" /> : getInitials(conv.name)}
                      </AvatarFallback>
                    </Avatar>
                    {conv.is_online && <div className="absolute bottom-0 right-0 h-3 w-3 bg-green-500 rounded-full border-2 border-white" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <p className="font-medium truncate">{conv.name}</p>
                      <span className="text-xs text-slate-500">{formatTime(conv.last_message_time)}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <p className="text-sm text-slate-500 truncate">{conv.last_message || 'No messages yet'}</p>
                      {conv.unread_count > 0 && (
                        <Badge className="bg-accent text-white rounded-full h-5 min-w-5 flex items-center justify-center text-xs">
                          {conv.unread_count}
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
              ))}
              {filteredConversations.length === 0 && !loading && (
                <div className="text-center text-slate-500 py-8">No conversations yet</div>
              )}
            </ScrollArea>
          </TabsContent>
          
          <TabsContent value="tasks" className="flex-1 overflow-hidden m-0">
            <div className="p-2">
              <Dialog open={showTaskDialog} onOpenChange={setShowTaskDialog}>
                <DialogTrigger asChild>
                  <Button size="sm" className="w-full"><Plus className="h-4 w-4 mr-2" />New Task</Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader><DialogTitle>Create Task</DialogTitle></DialogHeader>
                  <div className="space-y-4">
                    <div><Label>Title</Label><Input value={newTask.title} onChange={e => setNewTask({...newTask, title: e.target.value})} /></div>
                    <div><Label>Description</Label><Textarea value={newTask.description} onChange={e => setNewTask({...newTask, description: e.target.value})} /></div>
                    <div><Label>Assign To</Label>
                      <Select value={newTask.assigned_to} onValueChange={v => setNewTask({...newTask, assigned_to: v})}>
                        <SelectTrigger><SelectValue placeholder="Select user" /></SelectTrigger>
                        <SelectContent>{users.map(u => <SelectItem key={u.id} value={u.id}>{u.name || u.email}</SelectItem>)}</SelectContent>
                      </Select>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div><Label>Due Date</Label><Input type="date" value={newTask.due_date} onChange={e => setNewTask({...newTask, due_date: e.target.value})} /></div>
                      <div><Label>Priority</Label>
                        <Select value={newTask.priority} onValueChange={v => setNewTask({...newTask, priority: v})}>
                          <SelectTrigger><SelectValue /></SelectTrigger>
                          <SelectContent>
                            <SelectItem value="low">Low</SelectItem>
                            <SelectItem value="medium">Medium</SelectItem>
                            <SelectItem value="high">High</SelectItem>
                            <SelectItem value="urgent">Urgent</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                    <Button onClick={createTask} className="w-full">Create Task</Button>
                  </div>
                </DialogContent>
              </Dialog>
            </div>
            <ScrollArea className="h-[calc(100%-60px)]">
              {tasks.map(task => (
                <div key={task.id} className="p-3 border-b hover:bg-slate-50">
                  <div className="flex items-start gap-2">
                    <input 
                      type="checkbox" 
                      checked={task.status === 'completed'}
                      onChange={() => updateTaskStatus(task.id, task.status === 'completed' ? 'pending' : 'completed')}
                      className="mt-1"
                    />
                    <div className="flex-1">
                      <p className={`font-medium ${task.status === 'completed' ? 'line-through text-slate-400' : ''}`}>{task.title}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <Badge variant="outline" className={
                          task.priority === 'urgent' ? 'border-red-500 text-red-500' :
                          task.priority === 'high' ? 'border-orange-500 text-orange-500' :
                          task.priority === 'low' ? 'border-slate-400 text-slate-400' : ''
                        }>{task.priority}</Badge>
                        {task.due_date && <span className="text-xs text-slate-500"><Calendar className="h-3 w-3 inline mr-1" />{task.due_date}</span>}
                      </div>
                      <p className="text-xs text-slate-500 mt-1">→ {task.assigned_to_name}</p>
                    </div>
                  </div>
                </div>
              ))}
            </ScrollArea>
          </TabsContent>
        </Tabs>
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col border rounded-lg bg-white shadow-sm">
        {selectedChat ? (
          <>
            {/* Chat Header */}
            <div className="flex items-center justify-between p-4 border-b">
              <div className="flex items-center gap-3">
                <Avatar className="h-10 w-10">
                  <AvatarFallback className={selectedChat.type === 'group' ? 'bg-purple-500 text-white' : 'bg-accent text-white'}>
                    {selectedChat.type === 'group' ? <Users className="h-5 w-5" /> : getInitials(selectedChat.name)}
                  </AvatarFallback>
                </Avatar>
                <div>
                  <p className="font-semibold">{selectedChat.name}</p>
                  <p className="text-xs text-slate-500">
                    {selectedChat.type === 'group' ? `${selectedChat.member_count || 0} members` : 'Direct Message'}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Button size="sm" variant="ghost"><Phone className="h-4 w-4" /></Button>
                <Button size="sm" variant="ghost"><Video className="h-4 w-4" /></Button>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild><Button size="sm" variant="ghost"><MoreVertical className="h-4 w-4" /></Button></DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem><Star className="h-4 w-4 mr-2" />Star conversation</DropdownMenuItem>
                    <DropdownMenuItem><Pin className="h-4 w-4 mr-2" />Pin to top</DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem className="text-red-600">Clear chat</DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </div>

            {/* Messages */}
            <ScrollArea className="flex-1 p-4">
              <div className="space-y-4">
                {messages.map(msg => (
                  <div key={msg.id} className={`flex ${msg.sender_id === user?.id ? 'justify-end' : 'justify-start'}`}>
                    {msg.message_type === 'system' ? (
                      <div className="text-center text-xs text-slate-500 w-full py-2">{msg.content}</div>
                    ) : (
                      <div className={`max-w-[70%] ${msg.sender_id === user?.id ? 'order-2' : ''}`}>
                        {selectedChat.type === 'group' && msg.sender_id !== user?.id && (
                          <p className="text-xs text-slate-500 mb-1">{msg.sender_name}</p>
                        )}
                        <div className={`rounded-2xl px-4 py-2 ${
                          msg.sender_id === user?.id 
                            ? 'bg-accent text-white rounded-br-sm' 
                            : 'bg-slate-100 text-slate-900 rounded-bl-sm'
                        }`}>
                          <p>{msg.content}</p>
                          {msg.attachment_url && (
                            <a href={msg.attachment_url} target="_blank" rel="noopener noreferrer" className="text-sm underline">
                              📎 {msg.attachment_name || 'Attachment'}
                            </a>
                          )}
                        </div>
                        <div className={`flex items-center gap-1 mt-1 ${msg.sender_id === user?.id ? 'justify-end' : ''}`}>
                          <span className="text-xs text-slate-400">{formatTime(msg.created_at)}</span>
                          {msg.sender_id === user?.id && (
                            msg.is_read ? <CheckCheck className="h-3 w-3 text-blue-500" /> : <Check className="h-3 w-3 text-slate-400" />
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>
            </ScrollArea>

            {/* Input */}
            <form onSubmit={sendMessage} className="p-4 border-t">
              <div className="flex items-center gap-2">
                <Button type="button" size="sm" variant="ghost"><Smile className="h-5 w-5 text-slate-500" /></Button>
                <Button type="button" size="sm" variant="ghost"><Paperclip className="h-5 w-5 text-slate-500" /></Button>
                <Input 
                  value={newMessage}
                  onChange={e => setNewMessage(e.target.value)}
                  placeholder="Type a message..."
                  className="flex-1"
                />
                <Button type="submit" size="sm" disabled={!newMessage.trim()}>
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            </form>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-slate-500">
            <div className="text-center">
              <MessageSquare className="h-16 w-16 mx-auto mb-4 text-slate-300" />
              <p className="text-lg">Select a conversation or start a new chat</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Chat;
