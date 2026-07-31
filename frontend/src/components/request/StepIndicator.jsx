import { Check } from 'lucide-react';
import { clsx } from 'clsx';

export default function StepIndicator({ steps, currentStep }) {
  return (
    <nav aria-label="Progress" className="bg-white p-6 rounded-lg shadow-sm">
      <ol className="flex items-center">
        {steps.map((step, stepIdx) => (
          <li
            key={step.name}
            className={clsx(
              'relative flex items-center',
              stepIdx !== steps.length - 1 ? 'flex-1' : ''
            )}
          >
            <div className="flex items-center gap-3">
              <div
                className={clsx(
                  'flex h-10 w-10 items-center justify-center rounded-full border-2 transition-all z-10 bg-white',
                  step.number < currentStep
                    ? 'bg-primary-600 border-primary-600'
                    : step.number === currentStep
                    ? 'border-primary-600'
                    : 'border-gray-300'
                )}
              >
                {step.number < currentStep ? (
                  <Check className="h-6 w-6 text-white" />
                ) : (
                  <span
                    className={clsx(
                      'text-sm font-semibold',
                      step.number === currentStep
                        ? 'text-primary-600'
                        : 'text-gray-500'
                    )}
                  >
                    {step.number}
                  </span>
                )}
              </div>
              <div className="min-w-0 hidden sm:block">
                <p
                  className={clsx(
                    'text-sm font-medium whitespace-nowrap',
                    step.number <= currentStep
                      ? 'text-primary-600'
                      : 'text-gray-500'
                  )}
                >
                  {step.name}
                </p>
              </div>
            </div>
            {stepIdx !== steps.length - 1 && (
              <div className="flex-1 h-0.5 bg-gray-300 mx-4">
                <div
                  className={clsx(
                    'h-full bg-primary-600 transition-all duration-300',
                    step.number < currentStep ? 'w-full' : 'w-0'
                  )}
                />
              </div>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}
