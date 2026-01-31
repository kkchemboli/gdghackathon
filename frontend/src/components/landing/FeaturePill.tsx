import { LucideIcon } from 'lucide-react';

type PillVariant = 'teal' | 'yellow' | 'purple' | 'blue' | 'green';

interface FeaturePillProps {
  icon: LucideIcon;
  label: string;
  variant: PillVariant;
}

const FeaturePill = ({ icon: Icon, label, variant }: FeaturePillProps) => {
  return (
    <div className={`flex items-center gap-2 px-6 py-3 rounded-full font-medium pill-${variant}`}>
      <Icon className={`w-5 h-5 pill-${variant}-icon`} />
      <span>{label}</span>
    </div>
  );
};

export default FeaturePill;
