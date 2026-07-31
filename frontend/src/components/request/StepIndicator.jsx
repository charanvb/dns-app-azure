import { Check } from 'lucide-react';
import { clsx } from 'clsx';

export default function StepIndicator({ steps, currentStep }) {
  return (
    <nav aria-label="Progress">
      <ol className="flex items-center justify-between">
        {steps.map((step, stepIdx) => (
          <li
            key={step.name}
            className={clsx(
              stepIdx !== steps.length - 1 ? 'pr-8 sm:pr-20' : '',
              'relative flex-1'
            )}
          >
            <div className="flex items-center">
              <div className="relative flex items-center justify-center">
                <div
                  className={clsx(
                    'flex h-10 w-10 items-center justify-center rounded-full border-2 transition-all',
                    step.number < currentStep
                      ? 'bg-primary-600 border-primary-600'
                      : step.number === currentStep
                      ? 'border-primary-600 bg-white'
                      : 'border-gray-300 bg-white'
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
              </div>
              <div className="ml-4 min-w-0">
                <p
                  className={clsx(
                    'text-sm font-medium',
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
              <div className="absolute top-5 left-10 right-0 h-0.5 bg-gray-300">
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
