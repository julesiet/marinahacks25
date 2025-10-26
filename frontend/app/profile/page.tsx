import Link from "next/link"
import LoginButton from "../components/loginbutton"

export default function Profile() {

    return (
        <div className="flex flex-col justify-center items-center">
            <Link href="/"> go home bro </Link>
            <Link href="/builder"> WOOHOO! THE LINK! </Link>
        </div>
    )
}