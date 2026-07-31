import { forwardRef } from 'react';
import { clsx } from 'clsx';

const Input = forwardRef(({ 
  label, 
  error, 
  hint,
  required = false,
  as = 'input',
  className = '',
  ...props 
}, ref) => {
  const Component = as === 'textarea' ? 'textarea' : 'input';
  
  return (
    <div className="w-full">
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      {hint && <p className="text-xs text-gray-500 mb-1">{hint}</p>}
      <Component
        ref={ref}
        className={clsx(
          'input',
          as === 'textarea' && 'resize-vertical',
          error && 'border-red-500 focus:ring-red-500',
          className
        )}
        {...props}
      />
      {error && (
        <p className="mt-1 text-sm text-red-600">{error}</p>
      )}
    </div>
  );
});

Input.displayName = 'Input';

export default Input;
