import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from './ui/button';
import { Settings2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

/**
 * CustomizeFieldsButton - A button that navigates to Field Registry for a specific module/entity
 * Only visible to admin and director users
 * 
 * @param {Object} props
 * @param {string} props.module - The module identifier (e.g., 'crm')
 * @param {string} props.entity - The entity identifier (e.g., 'leads', 'accounts')
 * @param {string} props.variant - Button variant (default: 'ghost')
 * @param {string} props.size - Button size (default: 'sm')
 * @param {string} props.className - Additional CSS classes
 * @param {boolean} props.showLabel - Show text label (default: false)
 */
const CustomizeFieldsButton = ({ 
  module, 
  entity, 
  variant = 'ghost', 
  size = 'sm',
  className = '',
  showLabel = false
}) => {
  const navigate = useNavigate();
  const { user } = useAuth();
  
  // Only show for admin and director users
  if (!user || (user.role !== 'admin' && user.role !== 'director')) {
    return null;
  }

  const handleClick = () => {
    // Navigate to Field Registry with module and entity pre-selected
    navigate(`/field-registry?module=${module}&entity=${entity}`);
  };

  return (
    <Button
      variant={variant}
      size={size}
      onClick={handleClick}
      title={`Customize ${entity} fields`}
      className={`text-slate-500 hover:text-accent ${className}`}
      data-testid={`customize-fields-${entity}`}
    >
      <Settings2 className="h-4 w-4" />
      {showLabel && <span className="ml-2">Customize Fields</span>}
    </Button>
  );
};

export default CustomizeFieldsButton;
