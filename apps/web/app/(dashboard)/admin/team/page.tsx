"use client"

import { useState } from "react"
import { Navbar } from "@/components/dashboard/Navbar"
import { StatCard } from "@/components/dashboard/StatCard"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { UserPlus, Mail, Trash2, Shield, Copy, Clock, CheckCircle, XCircle } from "lucide-react"
import { toast } from "sonner"
import { copyToClipboard } from "@/lib/utils/copy"

interface TeamMember {
  id: string
  name: string
  email: string
  role: "super-user" | "admin" | "manager" | "staff" | "operator" | "customer-vip" | "customer"
  status: "active" | "pending" | "inactive"
  joined_at: string
  last_active: string
  invite_accepted: boolean
}

interface Invitation {
  id: string
  email: string
  role: string
  invited_by: string
  invited_at: string
  expires_at: string
  status: "pending" | "accepted" | "expired"
  invite_link: string
}

// Mock data
const mockTeamMembers: TeamMember[] = [
  {
    id: "user_1",
    name: "Admin User",
    email: "admin@example.com",
    role: "admin",
    status: "active",
    joined_at: "2025-01-01T00:00:00Z",
    last_active: "2025-11-08T14:30:00Z",
    invite_accepted: true
  },
  {
    id: "user_2",
    name: "Manager User",
    email: "manager@example.com",
    role: "manager",
    status: "active",
    joined_at: "2025-02-15T00:00:00Z",
    last_active: "2025-11-08T14:25:00Z",
    invite_accepted: true
  },
  {
    id: "user_3",
    name: "Staff User",
    email: "staff@example.com",
    role: "staff",
    status: "active",
    joined_at: "2025-03-20T00:00:00Z",
    last_active: "2025-11-08T14:20:00Z",
    invite_accepted: true
  },
  {
    id: "user_4",
    name: "New Member",
    email: "newmember@example.com",
    role: "operator",
    status: "pending",
    joined_at: "2025-11-05T00:00:00Z",
    last_active: "2025-11-05T00:00:00Z",
    invite_accepted: false
  },
]

const mockInvitations: Invitation[] = [
  {
    id: "inv_1",
    email: "pending@example.com",
    role: "staff",
    invited_by: "Admin User",
    invited_at: "2025-11-07T10:00:00Z",
    expires_at: "2025-11-14T10:00:00Z",
    status: "pending",
    invite_link: "https://rag-enterprise.com/invite/abc123def456"
  },
  {
    id: "inv_2",
    email: "accepted@example.com",
    role: "manager",
    invited_by: "Admin User",
    invited_at: "2025-11-01T10:00:00Z",
    expires_at: "2025-11-08T10:00:00Z",
    status: "accepted",
    invite_link: "https://rag-enterprise.com/invite/xyz789ghi012"
  },
]

export default function TeamManagementPage() {
  const [members, setMembers] = useState<TeamMember[]>(mockTeamMembers)
  const [invitations, setInvitations] = useState<Invitation[]>(mockInvitations)
  const [showInviteForm, setShowInviteForm] = useState(false)
  const [inviteEmail, setInviteEmail] = useState("")
  const [inviteRole, setInviteRole] = useState<string>("staff")
  const [inviteMessage, setInviteMessage] = useState("")

  // Stats
  const stats = {
    totalMembers: members.length,
    activeMembers: members.filter(m => m.status === "active").length,
    pendingInvites: invitations.filter(i => i.status === "pending").length,
    roles: new Set(members.map(m => m.role)).size
  }

  const getRoleColor = (role: string) => {
    const roleColors: Record<string, string> = {
      "super-user": "bg-stone-900 text-stone-100",
      "admin": "bg-stone-800 text-stone-100",
      "manager": "bg-stone-700 text-stone-100",
      "staff": "bg-stone-750 text-stone-100",
      "operator": "bg-stone-800 text-stone-100",
      "customer-vip": "bg-stone-850 text-stone-100",
      "customer": "bg-stone-700 text-stone-100"
    }
    return roleColors[role] || roleColors["customer"]
  }

  const getRoleLabel = (role: string) => {
    const labels: Record<string, string> = {
      "super-user": "Super-user",
      "admin": "Admin",
      "manager": "Manager",
      "staff": "Staff",
      "operator": "Operator",
      "customer-vip": "VIP",
      "customer": "Customer"
    }
    return labels[role] || role
  }

  const handleInvite = () => {
    if (!inviteEmail) {
      toast.error("이메일을 입력하세요")
      return
    }

    const newInvite: Invitation = {
      id: `inv_${Date.now()}`,
      email: inviteEmail,
      role: inviteRole,
      invited_by: "Current User",
      invited_at: new Date().toISOString(),
      expires_at: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
      status: "pending",
      invite_link: `https://rag-enterprise.com/invite/${Math.random().toString(36).substr(2, 12)}`
    }

    setInvitations([newInvite, ...invitations])
    toast.success(`초대장이 ${inviteEmail}로 전송되었습니다`)

    setInviteEmail("")
    setInviteMessage("")
    setShowInviteForm(false)
  }

  const handleRemoveMember = (id: string) => {
    setMembers(members.filter(m => m.id !== id))
    toast.success("팀원이 제거되었습니다")
  }

  const handleCancelInvite = (id: string) => {
    setInvitations(invitations.filter(i => i.id !== id))
    toast.success("초대가 취소되었습니다")
  }

  const handleChangeRole = (memberId: string, newRole: string) => {
    setMembers(members.map(m =>
      m.id === memberId ? { ...m, role: newRole as any } : m
    ))
    toast.success("역할이 변경되었습니다")
  }

  const getTimeRemaining = (expiresAt: string) => {
    const now = new Date()
    const expires = new Date(expiresAt)
    const diff = expires.getTime() - now.getTime()
    const days = Math.floor(diff / (1000 * 60 * 60 * 24))
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))

    if (diff < 0) return "만료됨"
    if (days > 0) return `${days}일 ${hours}시간 남음`
    return `${hours}시간 남음`
  }

  return (
    <div className="space-y-6 p-6">
      <Navbar
        title="팀 관리"
        subtitle="Team Management"
      />

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="전체 팀원"
          value={stats.totalMembers}
          
          subtitle="등록된 팀원 수"
        />
        <StatCard
          title="활성 팀원"
          value={stats.activeMembers}

          changeType="increase"
        />
        <StatCard
          title="대기 중인 초대"
          value={stats.pendingInvites}

          changeType={stats.pendingInvites > 0 ? "neutral" : "increase"}
        />
        <StatCard
          title="역할 종류"
          value={stats.roles}
          
          subtitle="사용 중인 역할"
        />
      </div>

      <Tabs defaultValue="members" className="space-y-4">
        <TabsList className="bg-stone-950">
          <TabsTrigger value="members">팀원</TabsTrigger>
          <TabsTrigger value="invitations">초대 관리</TabsTrigger>
          <TabsTrigger value="roles">역할 & 권한</TabsTrigger>
        </TabsList>

        {/* Members Tab */}
        <TabsContent value="members" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-stone-100">팀원 목록</CardTitle>
                  <CardDescription className="text-stone-400">
                    현재 팀에 속한 멤버 ({members.length}명)
                  </CardDescription>
                </div>
                <Button onClick={() => setShowInviteForm(!showInviteForm)} className="gap-2">
                  <UserPlus className="h-4 w-4" />
                  팀원 초대
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Invite Form */}
              {showInviteForm && (
                <Card className="bg-stone-900 border-stone-800">
                  <CardContent className="pt-6 space-y-4">
                    <div className="grid gap-4 md:grid-cols-2">
                      <div className="space-y-2">
                        <Label className="text-stone-300">이메일</Label>
                        <Input
                          type="email"
                          placeholder="user@example.com"
                          value={inviteEmail}
                          onChange={(e) => setInviteEmail(e.target.value)}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label className="text-stone-300">역할</Label>
                        <Select value={inviteRole} onValueChange={setInviteRole}>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="admin">Admin</SelectItem>
                            <SelectItem value="manager">Manager</SelectItem>
                            <SelectItem value="staff">Staff</SelectItem>
                            <SelectItem value="operator">Operator</SelectItem>
                            <SelectItem value="customer">Customer</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label className="text-stone-300">초대 메시지 (선택사항)</Label>
                      <Textarea
                        placeholder="팀에 오신 것을 환영합니다!"
                        value={inviteMessage}
                        onChange={(e) => setInviteMessage(e.target.value)}
                        rows={3}
                      />
                    </div>
                    <div className="flex gap-2">
                      <Button onClick={handleInvite} className="gap-2">
                        <Mail className="h-4 w-4" />
                        초대장 보내기
                      </Button>
                      <Button variant="outline" onClick={() => setShowInviteForm(false)}>
                        취소
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Members Table */}
              <Table>
                <TableHeader>
                  <TableRow className="border-stone-900 hover:bg-stone-950">
                    <TableHead className="text-stone-400">이름</TableHead>
                    <TableHead className="text-stone-400">이메일</TableHead>
                    <TableHead className="text-stone-400">역할</TableHead>
                    <TableHead className="text-stone-400">상태</TableHead>
                    <TableHead className="text-stone-400">가입일</TableHead>
                    <TableHead className="text-stone-400">마지막 활동</TableHead>
                    <TableHead className="text-stone-400">작업</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {members.map((member) => (
                    <TableRow key={member.id} className="border-stone-900 hover:bg-stone-950">
                      <TableCell className="font-medium text-stone-100">
                        {member.name}
                      </TableCell>
                      <TableCell className="text-stone-400">{member.email}</TableCell>
                      <TableCell>
                        <Select
                          value={member.role}
                          onValueChange={(value) => handleChangeRole(member.id, value)}
                        >
                          <SelectTrigger className="w-32">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="admin">Admin</SelectItem>
                            <SelectItem value="manager">Manager</SelectItem>
                            <SelectItem value="staff">Staff</SelectItem>
                            <SelectItem value="operator">Operator</SelectItem>
                          </SelectContent>
                        </Select>
                      </TableCell>
                      <TableCell>
                        {member.status === "active" ? (
                          <Badge className="bg-stone-700 text-stone-100">활성</Badge>
                        ) : member.status === "pending" ? (
                          <Badge className="bg-stone-800 text-stone-100">대기 중</Badge>
                        ) : (
                          <Badge className="bg-stone-700 text-stone-300">비활성</Badge>
                        )}
                      </TableCell>
                      <TableCell className="text-stone-400 text-sm">
                        {new Date(member.joined_at).toLocaleDateString("ko-KR")}
                      </TableCell>
                      <TableCell className="text-stone-400 text-sm">
                        {new Date(member.last_active).toLocaleString("ko-KR")}
                      </TableCell>
                      <TableCell>
                        <AlertDialog>
                          <AlertDialogTrigger asChild>
                            <Button variant="ghost" size="sm" className="text-stone-400 hover:text-stone-300">
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </AlertDialogTrigger>
                          <AlertDialogContent className="bg-stone-950 border-stone-800">
                            <AlertDialogHeader>
                              <AlertDialogTitle className="text-stone-100">팀원 제거</AlertDialogTitle>
                              <AlertDialogDescription className="text-stone-400">
                                {member.name}을(를) 팀에서 제거하시겠습니까? 이 작업은 되돌릴 수 없습니다.
                              </AlertDialogDescription>
                            </AlertDialogHeader>
                            <AlertDialogFooter>
                              <AlertDialogCancel className="bg-stone-900 text-stone-100">
                                취소
                              </AlertDialogCancel>
                              <AlertDialogAction
                                onClick={() => handleRemoveMember(member.id)}
                                className="bg-stone-900 text-stone-100 hover:bg-stone-800"
                              >
                                제거
                              </AlertDialogAction>
                            </AlertDialogFooter>
                          </AlertDialogContent>
                        </AlertDialog>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Invitations Tab */}
        <TabsContent value="invitations" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-stone-100">초대 관리</CardTitle>
              <CardDescription className="text-stone-400">
                보낸 초대 및 상태 확인 ({invitations.length}개)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow className="border-stone-900 hover:bg-stone-950">
                    <TableHead className="text-stone-400">이메일</TableHead>
                    <TableHead className="text-stone-400">역할</TableHead>
                    <TableHead className="text-stone-400">초대자</TableHead>
                    <TableHead className="text-stone-400">초대일</TableHead>
                    <TableHead className="text-stone-400">상태</TableHead>
                    <TableHead className="text-stone-400">만료</TableHead>
                    <TableHead className="text-stone-400">작업</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {invitations.map((invite) => (
                    <TableRow key={invite.id} className="border-stone-900 hover:bg-stone-950">
                      <TableCell className="text-stone-100">{invite.email}</TableCell>
                      <TableCell>
                        <Badge className={getRoleColor(invite.role)}>
                          {getRoleLabel(invite.role)}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-stone-400">{invite.invited_by}</TableCell>
                      <TableCell className="text-stone-400 text-sm">
                        {new Date(invite.invited_at).toLocaleDateString("ko-KR")}
                      </TableCell>
                      <TableCell>
                        {invite.status === "pending" ? (
                          <div className="flex items-center gap-1 text-stone-400">
                            <Clock className="h-4 w-4" />
                            <span className="text-sm">대기 중</span>
                          </div>
                        ) : invite.status === "accepted" ? (
                          <div className="flex items-center gap-1 text-stone-300">
                            <CheckCircle className="h-4 w-4" />
                            <span className="text-sm">수락됨</span>
                          </div>
                        ) : (
                          <div className="flex items-center gap-1 text-stone-500">
                            <XCircle className="h-4 w-4" />
                            <span className="text-sm">만료됨</span>
                          </div>
                        )}
                      </TableCell>
                      <TableCell className="text-stone-400 text-sm">
                        {getTimeRemaining(invite.expires_at)}
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              copyToClipboard(invite.invite_link)
                            }}
                          >
                            <Copy className="h-4 w-4" />
                          </Button>
                          {invite.status === "pending" && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleCancelInvite(invite.id)}
                              className="text-stone-400 hover:text-stone-300"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Roles Tab */}
        <TabsContent value="roles" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            {[
              {
                role: "super-user",
                label: "Super-user",
                description: "모든 권한 (시스템 설정, 사용자 관리, 감사 로그)",
                permissions: ["시스템 설정", "사용자 관리", "감사 로그", "모든 데이터 접근"]
              },
              {
                role: "admin",
                label: "Admin",
                description: "관리자 권한 (사용자 관리, 크롤링, 분석)",
                permissions: ["사용자 관리", "크롤링 관리", "데이터 분석", "API 키 관리"]
              },
              {
                role: "manager",
                label: "Manager",
                description: "매니저 권한 (크롤링, 분석, 읽기)",
                permissions: ["크롤링 시작", "데이터 분석", "결제 관리", "읽기 전용"]
              },
              {
                role: "staff",
                label: "Staff",
                description: "스태프 권한 (제조 관리, 품질 관리, 재고)",
                permissions: ["제조 관리", "품질 관리", "재고 관리", "제한된 접근"]
              },
              {
                role: "operator",
                label: "Operator",
                description: "운영자 권한 (제조, 품질 관리)",
                permissions: ["제조 관리", "품질 관리", "제한된 접근"]
              },
              {
                role: "customer",
                label: "Customer",
                description: "고객 권한 (제품 검색, 주문 내역)",
                permissions: ["제품 검색", "주문 내역", "고객 지원", "읽기 전용"]
              }
            ].map((roleInfo) => (
              <Card key={roleInfo.role}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <Badge className={getRoleColor(roleInfo.role)}>
                      {roleInfo.label}
                    </Badge>
                    <Shield className="h-5 w-5 text-stone-500" />
                  </div>
                  <CardTitle className="text-stone-100 text-lg">{roleInfo.label}</CardTitle>
                  <CardDescription className="text-stone-400">
                    {roleInfo.description}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <p className="text-sm font-medium text-stone-300">권한:</p>
                    <ul className="space-y-1">
                      {roleInfo.permissions.map((perm) => (
                        <li key={perm} className="flex items-center gap-2 text-sm text-stone-400">
                          <CheckCircle className="h-3 w-3 text-stone-400" />
                          {perm}
                        </li>
                      ))}
                    </ul>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
