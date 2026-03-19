import { useState } from 'react'
import { OutreachHeader } from '@/components/outreach/OutreachHeader'
import { SMSTemplateEditor } from '@/components/outreach/SMSTemplateEditor'
import { EmailTemplateEditor } from '@/components/outreach/EmailTemplateEditor'

export default function ConfigPage() {
  const [activeTab, setActiveTab] = useState<'sms' | 'email'>('sms')

  return (
    <div className="-m-8 flex h-[calc(100vh-var(--topnav-h,0px))] flex-col overflow-hidden">
      <OutreachHeader activeTab={activeTab} onTabChange={setActiveTab} />
      {activeTab === 'sms' ? <SMSTemplateEditor /> : <EmailTemplateEditor />}
    </div>
  )
}
