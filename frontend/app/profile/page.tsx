import Link from "next/link"
import LoginButton from "../components/loginbutton"

export default function Profile() {

    return (
        <div className="flex flex-col justify-center items-center">
            <LoginButton />
            <Link href="/"> go home bro </Link>
        </div>
    )
}