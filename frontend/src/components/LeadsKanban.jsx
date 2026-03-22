import React, { useState, useEffect } from 'react';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Phone, Mail, Calendar, User, Building2, MoreVertical, Edit, Eye } from 'lucide-react';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from './ui/dropdown-menu';

const statusColors = {
  new: { bg: 'bg-blue-50', border: 'border-blue-200', badge: 'bg-blue-100 text-blue-800', header: 'bg-blue-500' },
  contacted: { bg: 'bg-yellow-50', border: 'border-yellow-200', badge: 'bg-yellow-100 text-yellow-800', header: 'bg-yellow-500' },
  qualified: { bg: 'bg-green-50', border: 'border-green-200', badge: 'bg-green-100 text-green-800', header: 'bg-green-500' },
  proposal: { bg: 'bg-purple-50', border: 'border-purple-200', badge: 'bg-purple-100 text-purple-800', header: 'bg-purple-500' },
  negotiation: { bg: 'bg-orange-50', border: 'border-orange-200', badge: 'bg-orange-100 text-orange-800', header: 'bg-orange-500' },
  converted: { bg: 'bg-emerald-50', border: 'border-emerald-200', badge: 'bg-emerald-100 text-emerald-800', header: 'bg-emerald-500' },
  lost: { bg: 'bg-red-50', border: 'border-red-200', badge: 'bg-red-100 text-red-800', header: 'bg-red-500' }
};

const statusLabels = {
  new: 'New',
  contacted: 'Contacted',
  qualified: 'Qualified',
  proposal: 'Proposal',
  negotiation: 'Negotiation',
  converted: 'Converted',
  lost: 'Lost'
};

const LeadCard = ({ lead, index, onEdit, onView }) => {
  const colors = statusColors[lead.status] || statusColors.new;
  
  return (
    <Draggable draggableId={lead.id} index={index}>
      {(provided, snapshot) => (
        <div
          ref={provided.innerRef}
          {...provided.draggableProps}
          {...provided.dragHandleProps}
          className={`mb-3 ${snapshot.isDragging ? 'opacity-75' : ''}`}
        >
          <Card className={`${colors.bg} ${colors.border} border shadow-sm hover:shadow-md transition-shadow cursor-grab active:cursor-grabbing`}>
            <CardContent className="p-3">
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1 min-w-0">
                  <h4 className="font-semibold text-slate-900 text-sm truncate">{lead.company_name}</h4>
                  <p className="text-xs text-slate-500 truncate">{lead.contact_person}</p>
                </div>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                      <MoreVertical className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => onView?.(lead)}>
                      <Eye className="h-4 w-4 mr-2" />View Details
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => onEdit?.(lead)}>
                      <Edit className="h-4 w-4 mr-2" />Edit Lead
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
              
              <div className="space-y-1 text-xs text-slate-600">
                {lead.email && (
                  <div className="flex items-center gap-1 truncate">
                    <Mail className="h-3 w-3 flex-shrink-0" />
                    <span className="truncate">{lead.email}</span>
                  </div>
                )}
                {lead.phone && (
                  <div className="flex items-center gap-1">
                    <Phone className="h-3 w-3 flex-shrink-0" />
                    <span>{lead.phone}</span>
                  </div>
                )}
                {lead.product_interest && (
                  <div className="flex items-center gap-1 truncate">
                    <Building2 className="h-3 w-3 flex-shrink-0" />
                    <span className="truncate">{lead.product_interest}</span>
                  </div>
                )}
              </div>
              
              <div className="flex items-center justify-between mt-3 pt-2 border-t border-slate-200">
                <Badge className={`${colors.badge} text-xs`}>{lead.source}</Badge>
                {lead.estimated_value && (
                  <span className="text-xs font-semibold text-slate-700">
                    ₹{lead.estimated_value.toLocaleString('en-IN')}
                  </span>
                )}
              </div>
              
              {lead.next_followup_date && (
                <div className="flex items-center gap-1 mt-2 text-xs text-slate-500">
                  <Calendar className="h-3 w-3" />
                  <span>Follow-up: {new Date(lead.next_followup_date).toLocaleDateString()}</span>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </Draggable>
  );
};

const KanbanColumn = ({ status, leads, onEdit, onView }) => {
  const colors = statusColors[status] || statusColors.new;
  const label = statusLabels[status] || status;
  
  return (
    <div className="flex-shrink-0 w-72">
      <div className={`${colors.header} rounded-t-lg px-3 py-2`}>
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-white text-sm">{label}</h3>
          <Badge className="bg-white/20 text-white border-0">{leads.length}</Badge>
        </div>
      </div>
      <Droppable droppableId={status}>
        {(provided, snapshot) => (
          <div
            ref={provided.innerRef}
            {...provided.droppableProps}
            className={`${colors.bg} ${colors.border} border border-t-0 rounded-b-lg p-2 min-h-[400px] max-h-[calc(100vh-300px)] overflow-y-auto ${
              snapshot.isDraggingOver ? 'ring-2 ring-blue-400' : ''
            }`}
          >
            {leads.map((lead, index) => (
              <LeadCard 
                key={lead.id} 
                lead={lead} 
                index={index} 
                onEdit={onEdit}
                onView={onView}
              />
            ))}
            {provided.placeholder}
            {leads.length === 0 && (
              <div className="text-center py-8 text-slate-400 text-sm">
                No leads in this stage
              </div>
            )}
          </div>
        )}
      </Droppable>
    </div>
  );
};

const LeadsKanban = ({ data, columns, onMove, onEdit, onView, onRefresh }) => {
  const [kanbanData, setKanbanData] = useState(data || {});
  
  useEffect(() => {
    setKanbanData(data || {});
  }, [data]);
  
  const handleDragEnd = (result) => {
    const { destination, source, draggableId } = result;
    
    if (!destination) return;
    if (destination.droppableId === source.droppableId && destination.index === source.index) return;
    
    // Find the lead
    const sourceLeads = [...(kanbanData[source.droppableId] || [])];
    const [movedLead] = sourceLeads.splice(source.index, 1);
    
    if (!movedLead) return;
    
    // Update local state optimistically
    const newData = { ...kanbanData };
    newData[source.droppableId] = sourceLeads;
    
    const destLeads = source.droppableId === destination.droppableId 
      ? sourceLeads 
      : [...(kanbanData[destination.droppableId] || [])];
    
    movedLead.status = destination.droppableId;
    destLeads.splice(destination.index, 0, movedLead);
    newData[destination.droppableId] = destLeads;
    
    setKanbanData(newData);
    
    // Call API to persist change
    if (onMove) {
      onMove(draggableId, destination.droppableId);
    }
  };
  
  return (
    <DragDropContext onDragEnd={handleDragEnd}>
      <div className="flex gap-4 overflow-x-auto pb-4">
        {(columns || []).map((status) => (
          <KanbanColumn
            key={status}
            status={status}
            leads={kanbanData[status] || []}
            onEdit={onEdit}
            onView={onView}
          />
        ))}
      </div>
    </DragDropContext>
  );
};

export default LeadsKanban;
