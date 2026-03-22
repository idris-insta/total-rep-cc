import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '../components/ui/dialog';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSeparator } from '../components/ui/dropdown-menu';
import { Progress } from '../components/ui/progress';
import { 
  Folder, File, Upload, Search, Grid, List, Star, Clock, Users,
  MoreVertical, Download, Trash2, Share2, Eye, FolderPlus, ChevronRight,
  FileText, FileSpreadsheet, Image, Video, Music, Archive, FileCode,
  Home, HardDrive, StarOff, X, Check
} from 'lucide-react';
import api from '../lib/api';
import { toast } from 'sonner';

const Drive = () => {
  const [view, setView] = useState('grid');
  const [currentFolder, setCurrentFolder] = useState(null);
  const [folders, setFolders] = useState([]);
  const [files, setFiles] = useState([]);
  const [breadcrumb, setBreadcrumb] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [storageStats, setStorageStats] = useState(null);
  const [showNewFolder, setShowNewFolder] = useState(false);
  const [showUpload, setShowUpload] = useState(false);
  const [showShare, setShowShare] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);
  const [newFolderName, setNewFolderName] = useState('');
  const [uploadProgress, setUploadProgress] = useState(0);
  const [activeFilter, setActiveFilter] = useState('all');
  const [users, setUsers] = useState([]);
  const [shareUsers, setShareUsers] = useState([]);
  const [previewFile, setPreviewFile] = useState(null);

  useEffect(() => {
    fetchContent();
    fetchStorage();
    fetchUsers();
  }, [currentFolder, activeFilter]);

  const fetchContent = async () => {
    setLoading(true);
    try {
      // Fetch folders
      const foldersRes = await api.get(`/drive/folders${currentFolder ? `?parent_id=${currentFolder}` : ''}`);
      setFolders(foldersRes.data || []);
      
      // Fetch files with filters
      let fileUrl = `/drive/files?folder_id=${currentFolder || ''}`;
      if (activeFilter === 'favorites') fileUrl = '/drive/files?favorites_only=true';
      else if (activeFilter === 'recent') fileUrl = '/drive/files?recent=true';
      else if (activeFilter === 'shared') fileUrl = '/drive/files?shared_only=true';
      else if (['image', 'document', 'spreadsheet', 'pdf', 'video'].includes(activeFilter)) {
        fileUrl = `/drive/files?category=${activeFilter}`;
      }
      
      const filesRes = await api.get(fileUrl);
      setFiles(filesRes.data || []);
      
      // Fetch breadcrumb if in a folder
      if (currentFolder) {
        const folderRes = await api.get(`/drive/folders/${currentFolder}`);
        setBreadcrumb(folderRes.data.path || []);
      } else {
        setBreadcrumb([]);
      }
    } catch (err) {
      console.error('Failed to fetch content', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchStorage = async () => {
    try {
      const res = await api.get('/drive/storage');
      setStorageStats(res.data);
    } catch (err) {
      console.error('Failed to fetch storage', err);
    }
  };

  const fetchUsers = async () => {
    try {
      const res = await api.get('/chat/users');
      setUsers(res.data || []);
    } catch (err) {
      console.error('Failed to fetch users', err);
    }
  };

  const createFolder = async () => {
    if (!newFolderName.trim()) return;
    try {
      await api.post('/drive/folders', { name: newFolderName, parent_id: currentFolder });
      toast.success('Folder created');
      setShowNewFolder(false);
      setNewFolderName('');
      fetchContent();
    } catch (err) {
      toast.error('Failed to create folder');
    }
  };

  const handleUpload = async (e) => {
    const uploadFiles = e.target.files;
    if (!uploadFiles?.length) return;
    
    setShowUpload(true);
    setUploadProgress(0);
    
    for (let i = 0; i < uploadFiles.length; i++) {
      const file = uploadFiles[i];
      const formData = new FormData();
      formData.append('file', file);
      if (currentFolder) formData.append('folder_id', currentFolder);
      
      try {
        await api.post('/drive/upload', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
          onUploadProgress: (progressEvent) => {
            const progress = ((i + progressEvent.loaded / progressEvent.total) / uploadFiles.length) * 100;
            setUploadProgress(Math.round(progress));
          }
        });
      } catch (err) {
        toast.error(`Failed to upload ${file.name}`);
      }
    }
    
    toast.success('Upload complete');
    setShowUpload(false);
    fetchContent();
    fetchStorage();
  };

  const deleteItem = async (type, id) => {
    if (!confirm('Are you sure you want to delete this item?')) return;
    try {
      await api.delete(`/drive/${type}s/${id}`);
      toast.success('Deleted successfully');
      fetchContent();
      fetchStorage();
    } catch (err) {
      toast.error('Failed to delete');
    }
  };

  const toggleFavorite = async (type, id) => {
    try {
      await api.post(`/drive/${type}s/${id}/favorite`);
      fetchContent();
    } catch (err) {
      toast.error('Failed to update favorite');
    }
  };

  const shareItem = async () => {
    if (!selectedItem || shareUsers.length === 0) return;
    try {
      const endpoint = selectedItem.type === 'folder' 
        ? `/drive/folders/${selectedItem.id}/share`
        : `/drive/files/${selectedItem.id}/share`;
      await api.post(endpoint, { user_ids: shareUsers, permission: 'view' });
      toast.success('Shared successfully');
      setShowShare(false);
      setShareUsers([]);
    } catch (err) {
      toast.error('Failed to share');
    }
  };

  const downloadFile = async (fileId, fileName) => {
    try {
      const response = await api.get(`/drive/files/${fileId}/download`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', fileName);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      toast.error('Failed to download file');
    }
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const getFileIcon = (category) => {
    switch (category) {
      case 'image': return <Image className="h-8 w-8 text-green-500" />;
      case 'video': return <Video className="h-8 w-8 text-purple-500" />;
      case 'audio': return <Music className="h-8 w-8 text-pink-500" />;
      case 'pdf': return <FileText className="h-8 w-8 text-red-500" />;
      case 'spreadsheet': return <FileSpreadsheet className="h-8 w-8 text-green-600" />;
      case 'document': return <FileText className="h-8 w-8 text-blue-500" />;
      default: return <File className="h-8 w-8 text-slate-400" />;
    }
  };

  const filteredFiles = files.filter(f => f.name?.toLowerCase().includes(searchTerm.toLowerCase()));
  const filteredFolders = folders.filter(f => f.name?.toLowerCase().includes(searchTerm.toLowerCase()));

  return (
    <div className="flex gap-4 h-[calc(100vh-120px)]" data-testid="drive-page">
      {/* Sidebar */}
      <div className="w-56 flex flex-col bg-white rounded-lg border p-4">
        <input type="file" id="file-upload" className="hidden" multiple onChange={handleUpload} />
        <Button className="w-full mb-4" onClick={() => document.getElementById('file-upload').click()}>
          <Upload className="h-4 w-4 mr-2" />Upload
        </Button>
        
        <nav className="space-y-1 flex-1">
          <button onClick={() => { setCurrentFolder(null); setActiveFilter('all'); }} className={`w-full flex items-center gap-2 px-3 py-2 rounded text-left hover:bg-slate-100 ${!currentFolder && activeFilter === 'all' ? 'bg-slate-100' : ''}`}>
            <Home className="h-4 w-4" /><span>My Drive</span>
          </button>
          <button onClick={() => setActiveFilter('recent')} className={`w-full flex items-center gap-2 px-3 py-2 rounded text-left hover:bg-slate-100 ${activeFilter === 'recent' ? 'bg-slate-100' : ''}`}>
            <Clock className="h-4 w-4" /><span>Recent</span>
          </button>
          <button onClick={() => setActiveFilter('favorites')} className={`w-full flex items-center gap-2 px-3 py-2 rounded text-left hover:bg-slate-100 ${activeFilter === 'favorites' ? 'bg-slate-100' : ''}`}>
            <Star className="h-4 w-4" /><span>Favorites</span>
          </button>
          <button onClick={() => setActiveFilter('shared')} className={`w-full flex items-center gap-2 px-3 py-2 rounded text-left hover:bg-slate-100 ${activeFilter === 'shared' ? 'bg-slate-100' : ''}`}>
            <Users className="h-4 w-4" /><span>Shared with me</span>
          </button>
          
          <div className="border-t my-2 pt-2">
            <p className="text-xs text-slate-500 px-3 mb-2">File Types</p>
            {[
              { key: 'image', label: 'Images', icon: Image },
              { key: 'document', label: 'Documents', icon: FileText },
              { key: 'spreadsheet', label: 'Spreadsheets', icon: FileSpreadsheet },
              { key: 'pdf', label: 'PDFs', icon: FileText },
              { key: 'video', label: 'Videos', icon: Video }
            ].map(item => (
              <button key={item.key} onClick={() => setActiveFilter(item.key)} className={`w-full flex items-center gap-2 px-3 py-1.5 rounded text-left text-sm hover:bg-slate-100 ${activeFilter === item.key ? 'bg-slate-100' : ''}`}>
                <item.icon className="h-4 w-4" /><span>{item.label}</span>
              </button>
            ))}
          </div>
        </nav>
        
        {storageStats && (
          <div className="border-t pt-4 mt-4">
            <div className="flex items-center gap-2 mb-2">
              <HardDrive className="h-4 w-4 text-slate-500" />
              <span className="text-sm text-slate-600">Storage</span>
            </div>
            <Progress value={(storageStats.total_size / storageStats.storage_limit) * 100} className="h-2" />
            <p className="text-xs text-slate-500 mt-1">
              {formatFileSize(storageStats.total_size)} of {formatFileSize(storageStats.storage_limit)} used
            </p>
          </div>
        )}
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col bg-white rounded-lg border">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <div className="flex items-center gap-2">
            {breadcrumb.length > 0 ? (
              <div className="flex items-center gap-1">
                <button onClick={() => setCurrentFolder(null)} className="text-sm text-slate-500 hover:text-slate-900">My Drive</button>
                {breadcrumb.map((folder, idx) => (
                  <React.Fragment key={folder.id}>
                    <ChevronRight className="h-4 w-4 text-slate-400" />
                    <button onClick={() => setCurrentFolder(folder.id)} className={`text-sm ${idx === breadcrumb.length - 1 ? 'text-slate-900 font-medium' : 'text-slate-500 hover:text-slate-900'}`}>
                      {folder.name}
                    </button>
                  </React.Fragment>
                ))}
              </div>
            ) : (
              <h2 className="text-lg font-semibold">
                {activeFilter === 'all' ? 'My Drive' : activeFilter.charAt(0).toUpperCase() + activeFilter.slice(1)}
              </h2>
            )}
          </div>
          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input placeholder="Search..." className="pl-9 w-64" value={searchTerm} onChange={e => setSearchTerm(e.target.value)} />
            </div>
            <Dialog open={showNewFolder} onOpenChange={setShowNewFolder}>
              <DialogTrigger asChild>
                <Button variant="outline" size="sm"><FolderPlus className="h-4 w-4 mr-2" />New Folder</Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader><DialogTitle>Create Folder</DialogTitle></DialogHeader>
                <div className="space-y-4">
                  <div><Label>Folder Name</Label><Input value={newFolderName} onChange={e => setNewFolderName(e.target.value)} placeholder="Enter folder name" /></div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setShowNewFolder(false)}>Cancel</Button>
                  <Button onClick={createFolder}>Create</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
            <div className="flex border rounded">
              <button onClick={() => setView('grid')} className={`p-2 ${view === 'grid' ? 'bg-slate-100' : ''}`}><Grid className="h-4 w-4" /></button>
              <button onClick={() => setView('list')} className={`p-2 ${view === 'list' ? 'bg-slate-100' : ''}`}><List className="h-4 w-4" /></button>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-4">
          {loading ? (
            <div className="text-center py-8 text-slate-500">Loading...</div>
          ) : filteredFolders.length === 0 && filteredFiles.length === 0 ? (
            <div className="text-center py-16">
              <Folder className="h-16 w-16 mx-auto text-slate-300 mb-4" />
              <p className="text-slate-500">No files or folders here</p>
              <p className="text-sm text-slate-400">Upload files or create a folder to get started</p>
            </div>
          ) : view === 'grid' ? (
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
              {filteredFolders.map(folder => (
                <div key={folder.id} className="group relative border rounded-lg p-4 hover:shadow-md cursor-pointer transition-all" onDoubleClick={() => setCurrentFolder(folder.id)}>
                  <Folder className="h-12 w-12 text-amber-500 mx-auto mb-2" style={{ fill: folder.color || '#f59e0b' }} />
                  <p className="text-sm text-center truncate font-medium">{folder.name}</p>
                  {folder.is_favorite && <Star className="absolute top-2 right-2 h-4 w-4 text-amber-500 fill-amber-500" />}
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button size="sm" variant="ghost" className="absolute top-1 right-1 opacity-0 group-hover:opacity-100">
                        <MoreVertical className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent>
                      <DropdownMenuItem onClick={() => setCurrentFolder(folder.id)}><Folder className="h-4 w-4 mr-2" />Open</DropdownMenuItem>
                      <DropdownMenuItem onClick={() => toggleFavorite('folder', folder.id)}>{folder.is_favorite ? <StarOff className="h-4 w-4 mr-2" /> : <Star className="h-4 w-4 mr-2" />}{folder.is_favorite ? 'Remove from favorites' : 'Add to favorites'}</DropdownMenuItem>
                      <DropdownMenuItem onClick={() => { setSelectedItem({ ...folder, type: 'folder' }); setShowShare(true); }}><Share2 className="h-4 w-4 mr-2" />Share</DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem className="text-red-600" onClick={() => deleteItem('folder', folder.id)}><Trash2 className="h-4 w-4 mr-2" />Delete</DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              ))}
              {filteredFiles.map(file => (
                <div key={file.id} className="group relative border rounded-lg p-4 hover:shadow-md cursor-pointer transition-all">
                  <div className="mx-auto mb-2 flex justify-center">{getFileIcon(file.category)}</div>
                  <p className="text-sm text-center truncate" title={file.name}>{file.name}</p>
                  <p className="text-xs text-slate-400 text-center">{formatFileSize(file.file_size)}</p>
                  {file.is_favorite && <Star className="absolute top-2 right-2 h-4 w-4 text-amber-500 fill-amber-500" />}
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button size="sm" variant="ghost" className="absolute top-1 right-1 opacity-0 group-hover:opacity-100">
                        <MoreVertical className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent>
                      {['image', 'pdf'].includes(file.category) && (
                        <DropdownMenuItem onClick={() => setPreviewFile(file)}><Eye className="h-4 w-4 mr-2" />Preview</DropdownMenuItem>
                      )}
                      <DropdownMenuItem onClick={() => downloadFile(file.id, file.name)}><Download className="h-4 w-4 mr-2" />Download</DropdownMenuItem>
                      <DropdownMenuItem onClick={() => toggleFavorite('file', file.id)}>{file.is_favorite ? <StarOff className="h-4 w-4 mr-2" /> : <Star className="h-4 w-4 mr-2" />}{file.is_favorite ? 'Remove favorite' : 'Add favorite'}</DropdownMenuItem>
                      <DropdownMenuItem onClick={() => { setSelectedItem({ ...file, type: 'file' }); setShowShare(true); }}><Share2 className="h-4 w-4 mr-2" />Share</DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem className="text-red-600" onClick={() => deleteItem('file', file.id)}><Trash2 className="h-4 w-4 mr-2" />Delete</DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              ))}
            </div>
          ) : (
            <table className="w-full">
              <thead className="bg-slate-50">
                <tr>
                  <th className="text-left px-4 py-2 text-sm font-medium text-slate-600">Name</th>
                  <th className="text-left px-4 py-2 text-sm font-medium text-slate-600">Owner</th>
                  <th className="text-left px-4 py-2 text-sm font-medium text-slate-600">Modified</th>
                  <th className="text-left px-4 py-2 text-sm font-medium text-slate-600">Size</th>
                  <th className="w-10"></th>
                </tr>
              </thead>
              <tbody>
                {filteredFolders.map(folder => (
                  <tr key={folder.id} className="border-b hover:bg-slate-50 cursor-pointer" onDoubleClick={() => setCurrentFolder(folder.id)}>
                    <td className="px-4 py-3 flex items-center gap-2"><Folder className="h-5 w-5 text-amber-500" />{folder.name}{folder.is_favorite && <Star className="h-3 w-3 text-amber-500 fill-amber-500" />}</td>
                    <td className="px-4 py-3 text-sm text-slate-600">{folder.owner_name}</td>
                    <td className="px-4 py-3 text-sm text-slate-500">{new Date(folder.updated_at).toLocaleDateString()}</td>
                    <td className="px-4 py-3 text-sm text-slate-500">—</td>
                    <td className="px-4 py-3"><MoreVertical className="h-4 w-4 text-slate-400" /></td>
                  </tr>
                ))}
                {filteredFiles.map(file => (
                  <tr key={file.id} className="border-b hover:bg-slate-50">
                    <td className="px-4 py-3 flex items-center gap-2">{getFileIcon(file.category)}{file.name}{file.is_favorite && <Star className="h-3 w-3 text-amber-500 fill-amber-500" />}</td>
                    <td className="px-4 py-3 text-sm text-slate-600">{file.owner_name}</td>
                    <td className="px-4 py-3 text-sm text-slate-500">{new Date(file.updated_at).toLocaleDateString()}</td>
                    <td className="px-4 py-3 text-sm text-slate-500">{formatFileSize(file.file_size)}</td>
                    <td className="px-4 py-3"><MoreVertical className="h-4 w-4 text-slate-400" /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Share Dialog */}
      <Dialog open={showShare} onOpenChange={setShowShare}>
        <DialogContent>
          <DialogHeader><DialogTitle>Share "{selectedItem?.name}"</DialogTitle></DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Share with</Label>
              <div className="flex flex-wrap gap-1 mb-2">
                {shareUsers.map(id => {
                  const u = users.find(x => x.id === id);
                  return <Badge key={id} className="cursor-pointer" onClick={() => setShareUsers(shareUsers.filter(x => x !== id))}>{u?.name || 'User'} ×</Badge>;
                })}
              </div>
              <Select onValueChange={v => !shareUsers.includes(v) && setShareUsers([...shareUsers, v])}>
                <SelectTrigger><SelectValue placeholder="Select users to share with" /></SelectTrigger>
                <SelectContent>{users.filter(u => !shareUsers.includes(u.id)).map(u => <SelectItem key={u.id} value={u.id}>{u.name || u.email}</SelectItem>)}</SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowShare(false)}>Cancel</Button>
            <Button onClick={shareItem}>Share</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Upload Progress Dialog */}
      <Dialog open={showUpload}>
        <DialogContent>
          <DialogHeader><DialogTitle>Uploading...</DialogTitle></DialogHeader>
          <Progress value={uploadProgress} className="h-3" />
          <p className="text-center text-sm text-slate-500">{uploadProgress}% complete</p>
        </DialogContent>
      </Dialog>

      {/* Preview Dialog */}
      <Dialog open={!!previewFile} onOpenChange={() => setPreviewFile(null)}>
        <DialogContent className="max-w-4xl max-h-[90vh]">
          <DialogHeader><DialogTitle>{previewFile?.name}</DialogTitle></DialogHeader>
          <div className="flex justify-center items-center min-h-[400px]">
            {previewFile?.category === 'image' ? (
              <img src={`${api.defaults.baseURL}/drive/files/${previewFile.id}/preview`} alt={previewFile.name} className="max-w-full max-h-[70vh] object-contain" />
            ) : previewFile?.category === 'pdf' ? (
              <iframe src={`${api.defaults.baseURL}/drive/files/${previewFile.id}/preview`} className="w-full h-[70vh]" />
            ) : (
              <p className="text-slate-500">Preview not available for this file type</p>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Drive;
