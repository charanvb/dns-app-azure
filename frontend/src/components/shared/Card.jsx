import { clsx } from 'clsx';

export default function Card({ children, className = '', ...props }) {
  return (
    <div className={clsx('card p-6', className)} {...props}>
      {children}
    </div>
  );
}
